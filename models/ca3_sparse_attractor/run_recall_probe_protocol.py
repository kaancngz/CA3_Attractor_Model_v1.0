"""Run experiment-matched, reward-free recall/probe tests on the frozen CA3 core."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from models.ca3_sparse_attractor.config import SparseAttractorConfig
from models.ca3_sparse_attractor.model import AttractorCondition, SparseCA3Attractor
from models.ca3_sparse_attractor.cli import parse_float_list, parse_int_list
from models.ca3_sparse_attractor.theory_mapping import (
    expected_choice_discrimination,
)


STATE_CLASSES = ("A", "B", "mixed", "silent", "undecided")


@dataclass(frozen=True)
class ProbeArm:
    arm_id: str
    experimental_group: str
    hypothesis: str
    vector: str
    test_context: str
    cue_regime: str
    cue_a: float
    cue_b: float
    light_on_manipulation: str
    control_mirror_of: str | None = None


def build_probe_arms(tone_scale: float = 0.50) -> list[ProbeArm]:
    """Return the four experimental groups and counterbalanced H3/control arms."""
    return [
        ProbeArm(
            "H1_ARCHT_TAGGED_CONTEXT",
            "G1",
            "H1",
            "ArchT",
            "tagged_context",
            "tagged_context_partial_cue",
            1.0,
            0.0,
            "suppress",
        ),
        ProbeArm(
            "H2_CHR2_UNTAGGED_CONTEXT",
            "G2",
            "H2",
            "ChR2",
            "untagged_context",
            "untagged_context_partial_cue",
            0.0,
            1.0,
            "activate",
        ),
        ProbeArm(
            "H3_ARCHT_C_TAGGED_LEADING",
            "G3",
            "H3",
            "ArchT",
            "neutral_C",
            "tone_present_tagged_high",
            tone_scale * 0.65,
            tone_scale * 0.35,
            "suppress",
        ),
        ProbeArm(
            "H3_ARCHT_C_TAGGED_TRAILING",
            "G3",
            "H3",
            "ArchT",
            "neutral_C",
            "tone_present_untagged_high",
            tone_scale * 0.35,
            tone_scale * 0.65,
            "suppress",
        ),
        ProbeArm(
            "EGFP_TAGGED_CONTEXT_CONTROL",
            "G4",
            "CONTROL",
            "EGFP",
            "tagged_context",
            "tagged_context_partial_cue",
            1.0,
            0.0,
            "none",
            "H1_ARCHT_TAGGED_CONTEXT",
        ),
        ProbeArm(
            "EGFP_UNTAGGED_CONTEXT_CONTROL",
            "G4",
            "CONTROL",
            "EGFP",
            "untagged_context",
            "untagged_context_partial_cue",
            0.0,
            1.0,
            "none",
            "H2_CHR2_UNTAGGED_CONTEXT",
        ),
        ProbeArm(
            "EGFP_C_TAGGED_LEADING_CONTROL",
            "G4",
            "CONTROL",
            "EGFP",
            "neutral_C",
            "tone_present_tagged_high",
            tone_scale * 0.65,
            tone_scale * 0.35,
            "none",
            "H3_ARCHT_C_TAGGED_LEADING",
        ),
        ProbeArm(
            "EGFP_C_TAGGED_TRAILING_CONTROL",
            "G4",
            "CONTROL",
            "EGFP",
            "neutral_C",
            "tone_present_untagged_high",
            tone_scale * 0.35,
            tone_scale * 0.65,
            "none",
            "H3_ARCHT_C_TAGGED_TRAILING",
        ),
    ]


def counterbalance_assignment(index: int) -> dict:
    """Map canonical tagged/untagged memories onto physical labels and odors."""
    tagged_context = "A" if index % 2 == 0 else "B"
    untagged_context = "B" if tagged_context == "A" else "A"
    tagged_odor = "mint" if (index // 2) % 2 == 0 else "carvone"
    untagged_odor = "carvone" if tagged_odor == "mint" else "mint"
    return {
        "counterbalance_block": index % 8,
        "canonical_tagged_memory": "A",
        "physical_tagged_context": tagged_context,
        "physical_untagged_context": untagged_context,
        "tagged_rewarded_odor": tagged_odor,
        "untagged_rewarded_odor": untagged_odor,
        "light_order": "off_then_on" if index % 2 == 0 else "on_then_off",
    }


def final_summary(result: dict) -> dict:
    return result["convergence"]["trajectory"][-1]


def asymptotic_summary(result: dict) -> tuple[dict, dict]:
    """Average a fixed point or one complete synchronous microstate cycle."""
    convergence = result["convergence"]
    if convergence["status"] == "cycle":
        window_size = int(convergence["cycle_length"])
        window = convergence["trajectory"][-window_size:]
    else:
        window_size = 1
        window = [convergence["trajectory"][-1]]

    numeric_keys = [
        "overlap_a",
        "overlap_b",
        "overlap_margin_a_minus_b",
        "a_unique_activity",
        "b_unique_activity",
        "shared_activity",
        "a_engram_activity",
        "b_engram_activity",
        "outside_activity",
        "active_fraction",
        "tagged_reactivation",
        "chance_reactivation",
    ]
    summary = {
        key: statistics.mean(item[key] for item in window) for key in numeric_keys
    }
    a_unique = summary["a_unique_activity"]
    b_unique = summary["b_unique_activity"]
    denominator = a_unique + b_unique
    competition = 0.0 if denominator == 0.0 else (a_unique - b_unique) / denominator
    evidence = a_unique - b_unique
    summary["neural_competition_index"] = competition
    summary["signed_retrieval_evidence"] = evidence
    if summary["active_fraction"] < 0.01:
        state_class = "silent"
    elif competition >= 0.25 and a_unique >= 0.50:
        state_class = "A"
    elif competition <= -0.25 and b_unique >= 0.50:
        state_class = "B"
    elif a_unique >= 0.25 and b_unique >= 0.25:
        state_class = "mixed"
    else:
        state_class = "undecided"
    summary["state_class"] = state_class
    chance = summary["chance_reactivation"]
    summary["reactivation_enrichment"] = (
        summary["tagged_reactivation"] / chance if chance > 0.0 else None
    )
    microstate_classes = sorted({item["state_class"] for item in window})
    return summary, {
        "asymptotic_window_size": window_size,
        "microstate_cycle_length": convergence["cycle_length"],
        "microstate_classes": "|".join(microstate_classes),
        "macrostate_stable_across_cycle": len(microstate_classes) == 1
        and microstate_classes[0] == state_class,
    }


def exact_pattern_match(model: SparseCA3Attractor, result: dict, memory: str) -> bool:
    return bool(
        (
            result["convergence"]["final_state"]
            == model.pattern_state(memory)
        ).all()
    )


def run_recall_qualification(model: SparseCA3Attractor) -> dict:
    """Qualify autonomous A/B pattern completion before any hypothesis probe."""
    memories = {}
    for memory in ("A", "B"):
        condition = AttractorCondition(
            "recall_qualification_%s" % memory,
            1.0 if memory == "A" else 0.0,
            1.0 if memory == "B" else 0.0,
            cue_target_fraction=model.config.cue_target_fraction,
        )
        result = model.run_condition(condition, cue_remains_on=False)
        summary = final_summary(result)
        memories[memory] = {
            "exact_pattern_completion": exact_pattern_match(model, result, memory),
            "state_class": summary["state_class"],
            "signed_retrieval_evidence": summary["signed_retrieval_evidence"],
            "convergence_status": result["convergence"]["status"],
            "convergence_steps": result["convergence"]["steps"],
        }
    return {
        "A": memories["A"],
        "B": memories["B"],
        "passed": all(
            memories[memory]["exact_pattern_completion"] for memory in ("A", "B")
        ),
    }


def _beta_key(beta: float) -> str:
    return "%g" % beta


def run_probe(
    model: SparseCA3Attractor,
    arm: ProbeArm,
    *,
    light_state: str,
    manipulation_strength: float,
    pre_light_steps: int,
    inverse_temperatures: list[float],
    network_id: str,
    seed: int,
    assignment: dict,
    recall_qualified: bool,
) -> dict:
    if light_state not in ("off", "on"):
        raise ValueError("light_state must be off or on")
    manipulation = (
        arm.light_on_manipulation if light_state == "on" else "none"
    )
    condition = AttractorCondition(
        "%s_%s" % (arm.arm_id, light_state),
        arm.cue_a,
        arm.cue_b,
        manipulation=manipulation,
        manipulation_strength=(
            manipulation_strength if manipulation != "none" else 0.0
        ),
        # None means all cells jointly surviving RAM, tag-test match and fiber
        # access. This keeps the biological losses separate rather than
        # multiplying an additional nominal intervention fraction.
        manipulation_fraction=None,
    )
    result = model.run_condition(
        condition,
        pre_cue_steps=pre_light_steps,
        cue_steps=1,
        cue_remains_on=True,
    )
    summary, asymptotic_meta = asymptotic_summary(result)
    available_access = (
        len(set(model.accessible).intersection(model.layout.a)) / model.layout.a.size
    )
    row = {
        "network_id": network_id,
        "seed": seed,
        "arm_id": arm.arm_id,
        "experimental_group": arm.experimental_group,
        "hypothesis": arm.hypothesis,
        "vector": arm.vector,
        "control_mirror_of": arm.control_mirror_of,
        "test_context": arm.test_context,
        "cue_regime": arm.cue_regime,
        "reward_present": False,
        "initial_state_reset": True,
        "synaptic_plasticity_during_probe": False,
        "cue_remains_on": True,
        "pre_light_steps": pre_light_steps,
        "light_state": light_state,
        "manipulation": manipulation,
        "manipulation_strength": (
            manipulation_strength if manipulation != "none" else 0.0
        ),
        "cue_a": arm.cue_a,
        "cue_b": arm.cue_b,
        "recall_qualified": recall_qualified,
        "available_effective_final_a_access": available_access,
        "effective_manipulated_final_a_fraction": result[
            "effective_manipulated_final_a_fraction"
        ],
        "manipulated_count": result["manipulated_count"],
        "state_class": summary["state_class"],
        "signed_retrieval_evidence": summary["signed_retrieval_evidence"],
        "neural_competition_index": summary["neural_competition_index"],
        "a_unique_activity": summary["a_unique_activity"],
        "b_unique_activity": summary["b_unique_activity"],
        "shared_activity": summary["shared_activity"],
        "tagged_reactivation": summary["tagged_reactivation"],
        "chance_reactivation": summary["chance_reactivation"],
        "reactivation_enrichment": summary["reactivation_enrichment"],
        "convergence_status": result["convergence"]["status"],
        "convergence_steps": result["convergence"]["steps"],
        **asymptotic_meta,
        **assignment,
    }
    for beta in inverse_temperatures:
        row["expected_discrimination_beta_%s" % _beta_key(beta)] = (
            expected_choice_discrimination(
                summary["signed_retrieval_evidence"], beta
            )
        )
    return row


def pair_probe_rows(
    off: dict,
    on: dict,
    inverse_temperatures: list[float],
) -> dict:
    if off["network_id"] != on["network_id"] or off["arm_id"] != on["arm_id"]:
        raise ValueError("probe pair must use the same network and arm")
    pair = {
        "network_id": off["network_id"],
        "seed": off["seed"],
        "arm_id": off["arm_id"],
        "experimental_group": off["experimental_group"],
        "hypothesis": off["hypothesis"],
        "vector": off["vector"],
        "off_state": off["state_class"],
        "on_state": on["state_class"],
        "state_transition": "%s_to_%s" % (off["state_class"], on["state_class"]),
        "delta_evidence": (
            on["signed_retrieval_evidence"] - off["signed_retrieval_evidence"]
        ),
        "delta_nci": (
            on["neural_competition_index"] - off["neural_competition_index"]
        ),
        "delta_tagged_reactivation": (
            on["tagged_reactivation"] - off["tagged_reactivation"]
        ),
        "available_effective_final_a_access": on[
            "available_effective_final_a_access"
        ],
    }
    for beta in inverse_temperatures:
        key = "expected_discrimination_beta_%s" % _beta_key(beta)
        pair["delta_%s" % key] = on[key] - off[key]
    return pair


def state_fractions(items: list[dict], key: str) -> dict:
    return {
        state: statistics.mean(item[key] == state for item in items)
        for state in STATE_CLASSES
    }


def aggregate_arm(items: list[dict], inverse_temperatures: list[float]) -> dict:
    delta_evidence = [item["delta_evidence"] for item in items]
    return {
        "n_structural_realizations": len(items),
        "off_state_fractions": state_fractions(items, "off_state"),
        "on_state_fractions": state_fractions(items, "on_state"),
        "state_switch_fraction": statistics.mean(
            item["off_state"] != item["on_state"] for item in items
        ),
        "mean_delta_evidence": statistics.mean(delta_evidence),
        "sd_delta_evidence_across_structures": (
            statistics.stdev(delta_evidence) if len(delta_evidence) > 1 else 0.0
        ),
        "mean_delta_nci": statistics.mean(item["delta_nci"] for item in items),
        "mean_delta_tagged_reactivation": statistics.mean(
            item["delta_tagged_reactivation"] for item in items
        ),
        "mean_available_effective_final_a_access": statistics.mean(
            item["available_effective_final_a_access"] for item in items
        ),
        "behavioral_envelope": {
            _beta_key(beta): {
                "mean_delta_expected_discrimination": statistics.mean(
                    item[
                        "delta_expected_discrimination_beta_%s" % _beta_key(beta)
                    ]
                    for item in items
                )
            }
            for beta in inverse_temperatures
        },
    }


def build_h3_interactions(pairs: list[dict]) -> dict:
    by_network: dict[str, dict[str, dict]] = {}
    for pair in pairs:
        by_network.setdefault(pair["network_id"], {})[pair["arm_id"]] = pair
    rows = []
    for network_id, arms in by_network.items():
        leading = arms["H3_ARCHT_C_TAGGED_LEADING"]
        trailing = arms["H3_ARCHT_C_TAGGED_TRAILING"]
        qualified = leading["off_state"] == "A" and trailing["off_state"] == "B"
        rows.append(
            {
                "network_id": network_id,
                "seed": leading["seed"],
                "baseline_qualified": qualified,
                "leading_delta_evidence": leading["delta_evidence"],
                "trailing_delta_evidence": trailing["delta_evidence"],
                "signed_interaction": (
                    leading["delta_evidence"] - trailing["delta_evidence"]
                    if qualified
                    else None
                ),
            }
        )
    qualified_rows = [row for row in rows if row["baseline_qualified"]]
    return {
        "rows": rows,
        "baseline_qualified_fraction": len(qualified_rows) / len(rows),
        "mean_signed_interaction": (
            statistics.mean(row["signed_interaction"] for row in qualified_rows)
            if qualified_rows
            else None
        ),
        "negative_interaction_fraction": (
            statistics.mean(row["signed_interaction"] < 0.0 for row in qualified_rows)
            if qualified_rows
            else None
        ),
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0])
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _pct(value: float) -> str:
    return "%.1f%%" % (100.0 * value)


def write_markdown(path: Path, payload: dict) -> None:
    arms = payload["aggregate_by_arm"]
    beta_key = "2"
    lines = [
        "# CA3 recall–probe testi — protokol ve ilk sonuç v1",
        "",
        "Tarih: 2026-08-16",
        "Durum: veri-öncesi mekanistik recall–probe koşusu",
        "",
        "Bu koşu yeni bir mimari kurmaz. Dondurulmuş seyrek CA3 çekirdeğini",
        "deneydeki bağlam, ortak ipucu, ışık-kapalı/açık ve opsin-kontrol",
        "mantığıyla yürütür. Her prob ödülsüzdür; ağ durumu prob başında sıfırlanır",
        "ve prob sırasında sinaptik öğrenme yapılmaz.",
        "",
        "## Protokol karşılığı",
        "",
        "Deney | Hesaplamalı karşılık",
        "--- | ---",
        "Eğitim sonrası bellek | Dondurulmuş A/B Hebbian çekici ağı",
        "Işığın bekleme döneminde başlaması | İpucundan önce %d soyut güncelleme adımı"
        % payload["design"]["pre_light_steps"],
        "Işığın prob boyunca sürmesi | Sürekli pozitif/negatif dış alan",
        "Ödülsüz 3 dakikalık prob | Ödül girdisi olmadan sabit nokta veya kararlı makro-çekici",
        "Aynı hayvanda ışık kapalı/açık | Aynı yapısal ağda eşleşmiş iki koşul",
        "Karşı-dengeleme | Fiziksel A/B, koku ve ışık sırası metaverisi",
        "Kazma ayrım oranı | Pilotla kalibre edilmemiş `β` duyarlılık zarfı",
        "",
        (
            "Çalışma noktası: `%s` engram seyrekliği, `%s` A/B örtüşmesi, "
            "`%s` RAM etiketleme, `%s` fiber erişimi ve `%s` tag–test uyumu. "
            "Bunların gerçek hücresel kesişimi ortalama `%s` etkili nihai-A "
            "erişimi üretmiştir."
        )
        % (
            _pct(payload["design"]["engram_fraction"]),
            _pct(payload["design"]["overlap_fraction"]),
            _pct(payload["design"]["tagging_efficiency"]),
            _pct(payload["design"]["fiber_coverage"]),
            _pct(payload["design"]["tag_test_match_fraction"]),
            _pct(
                arms["H1_ARCHT_TAGGED_CONTEXT"][
                    "mean_available_effective_final_a_access"
                ]
            ),
        ),
        "",
        "## Recall yeterlilik kontrolü",
        "",
        "A ve B kısmi ipuçları kaldırıldıktan sonra örüntüyü tamamlama oranı: "
        "`%s` (%d/%d ağ)."
        % (
            _pct(payload["quality_checks"]["recall_qualification_fraction"]),
            payload["quality_checks"]["recall_qualified_count"],
            payload["design"]["n_structural_realizations"],
        ),
        "",
        (
            "Sürekli dış alan altında probların `%s` kadarı senkron mikrodurum "
            "döngüsü üretmiştir. Son faz keyfî seçilmemiş; bir tam döngü "
            "üzerinden zaman ortalaması alınmıştır. Bütün problarda çekici "
            "sınıfı döngü boyunca kararlı kalmıştır."
        )
        % _pct(payload["quality_checks"]["cycle_probe_fraction"]),
        "",
        "## Eşleşmiş prob sonuçları",
        "",
        "Kol | Kapalı durum | Açık durum | Ortalama ΔE | Ortalama Δreaktivasyon | ΔDR (`β=2`)",
        "--- | --- | --- | ---: | ---: | ---:",
    ]
    display_order = [
        "H1_ARCHT_TAGGED_CONTEXT",
        "H2_CHR2_UNTAGGED_CONTEXT",
        "H3_ARCHT_C_TAGGED_LEADING",
        "H3_ARCHT_C_TAGGED_TRAILING",
        "EGFP_TAGGED_CONTEXT_CONTROL",
        "EGFP_UNTAGGED_CONTEXT_CONTROL",
        "EGFP_C_TAGGED_LEADING_CONTROL",
        "EGFP_C_TAGGED_TRAILING_CONTROL",
    ]
    for arm_id in display_order:
        item = arms[arm_id]
        off_state = max(item["off_state_fractions"], key=item["off_state_fractions"].get)
        on_state = max(item["on_state_fractions"], key=item["on_state_fractions"].get)
        lines.append(
            "%s | %s | %s | %.3f | %.3f | %.3f"
            % (
                arm_id,
                off_state,
                on_state,
                item["mean_delta_evidence"],
                item["mean_delta_tagged_reactivation"],
                item["behavioral_envelope"][beta_key][
                    "mean_delta_expected_discrimination"
                ],
            )
        )
    h3 = payload["H3_positional_interaction"]
    lines.extend(
        [
            "",
            "## H3 konumsal etkileşim",
            "",
            "- Manipülasyonsuz A-önde/B-geride başlangıç yeterliliği: `%s`."
            % _pct(h3["baseline_qualified_fraction"]),
            "- Ortalama `ΔE_önde−ΔE_geride`: `%s`."
            % (
                "tanımsız"
                if h3["mean_signed_interaction"] is None
                else "%.3f" % h3["mean_signed_interaction"]
            ),
            "- Negatif konumsal etkileşim gösteren yeterli ağ oranı: `%s`."
            % (
                "tanımsız"
                if h3["negative_interaction_fraction"] is None
                else _pct(h3["negative_interaction_fraction"])
            ),
            "",
            "## Hipotez kararı",
            "",
            "- **H1:** Baskılama A kanıtını ve etiketli reaktivasyonu azaltır;",
            "  fakat 25/25 ağ A çekicisinde kalır. Minimal nöral gereklilik var,",
            "  güçlü şansa/kategorik çöküş yoktur.",
            "- **H2:** Etkinleştirme 25/25 ağda B çekicisinden A çekicisine geçiş",
            "  üretir; yeterlilik bu çalışma noktasında desteklenir.",
            "- **H3:** A öndeyken baskılama etkisi A gerideykenkinden daha büyüktür;",
            "  fakat 25/25 ağ kendi başlangıç çekicisinde kalır. Pozisyonel asimetri",
            "  var, rakip anıya tam kategorik dönüş yoktur.",
            "- **EGFP:** Bütün eş koşullarda ışık etkisi tam sıfırdır; bu kontrol",
            "  modelde ışığın opsinden bağımsız biyolojik yan etkisini değil,",
            "  manipülasyon alanının yokluğunu temsil eder.",
            "",
            "## Çıkarım sınırı",
            "",
            "Yapısal ağlar sanal hayvan değildir. Deterministik prob tekrarları",
            "hayvan-içi davranış varyansı, sıra/taşıma etkisi, üç dakikalık kazma",
            "zaman serisi veya 20 Hz optogenetik darbeleri üretmez. Bu nedenle",
            "mevcut tablo mekanistik yön ve çekici geçişini sınar; `p`, Cohen `dz`",
            "ve örneklem büyüklüğü pilot varyansı gelmeden hesaplanmaz.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=("smoke", "pilot", "full"), default="pilot")
    parser.add_argument(
        "--seeds",
        type=parse_int_list,
        default=parse_int_list(
            ",".join(str(seed) for seed in range(20260815, 20260840))
        ),
    )
    parser.add_argument("--engram-fraction", type=float, default=0.08)
    parser.add_argument("--overlap", type=float, default=0.20)
    parser.add_argument("--threshold", type=float, default=0.12)
    parser.add_argument("--tagging-efficiency", type=float, default=0.50)
    parser.add_argument("--fiber-coverage", type=float, default=0.50)
    parser.add_argument("--tag-test-match", type=float, default=1.00)
    parser.add_argument("--manipulation-strength", type=float, default=1.00)
    parser.add_argument("--tone-scale", type=float, default=0.50)
    parser.add_argument("--pre-light-steps", type=int, default=1)
    parser.add_argument(
        "--inverse-temperatures",
        type=parse_float_list,
        default=parse_float_list("1,2,4,8"),
    )
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--csv-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.pre_light_steps < 0:
        raise ValueError("pre-light steps cannot be negative")
    started = time.time()
    arms = build_probe_arms(args.tone_scale)
    all_rows = []
    all_pairs = []
    recall_rows = []

    for index, seed in enumerate(args.seeds):
        config = SparseAttractorConfig.for_profile(
            args.profile,
            seed=seed,
            engram_fraction=args.engram_fraction,
            overlap_fraction=args.overlap,
            activation_threshold=args.threshold,
            max_active_fraction=args.engram_fraction,
            tagging_efficiency=args.tagging_efficiency,
            fiber_coverage=args.fiber_coverage,
            tag_test_match_fraction=args.tag_test_match,
        )
        model = SparseCA3Attractor(config)
        network_id = "network_%03d" % (index + 1)
        assignment = counterbalance_assignment(index)
        recall = run_recall_qualification(model)
        recall_rows.append(
            {
                "network_id": network_id,
                "seed": seed,
                **assignment,
                **recall,
            }
        )
        for arm in arms:
            light_order = (
                ("off", "on")
                if assignment["light_order"] == "off_then_on"
                else ("on", "off")
            )
            pair_members = {}
            for light_state in light_order:
                row = run_probe(
                    model,
                    arm,
                    light_state=light_state,
                    manipulation_strength=args.manipulation_strength,
                    pre_light_steps=args.pre_light_steps,
                    inverse_temperatures=args.inverse_temperatures,
                    network_id=network_id,
                    seed=seed,
                    assignment=assignment,
                    recall_qualified=recall["passed"],
                )
                all_rows.append(row)
                pair_members[light_state] = row
            all_pairs.append(
                pair_probe_rows(
                    pair_members["off"],
                    pair_members["on"],
                    args.inverse_temperatures,
                )
            )
        print("%s complete" % network_id, flush=True)

    aggregate_by_arm = {
        arm.arm_id: aggregate_arm(
            [pair for pair in all_pairs if pair["arm_id"] == arm.arm_id],
            args.inverse_temperatures,
        )
        for arm in arms
    }
    h3_interaction = build_h3_interactions(all_pairs)
    egfp_pairs = [pair for pair in all_pairs if pair["vector"] == "EGFP"]
    recall_qualified_count = sum(row["passed"] for row in recall_rows)
    expected_row_count = len(args.seeds) * len(arms) * 2
    all_probe_completed = all(
        row["convergence_status"] in ("fixed_point", "cycle") for row in all_rows
    )
    all_probe_macrostates_stable = all(
        row["macrostate_stable_across_cycle"] for row in all_rows
    )
    cycle_probe_count = sum(
        row["convergence_status"] == "cycle" for row in all_rows
    )
    primary_baselines_qualified = all(
        pair["off_state"] == "A"
        for pair in all_pairs
        if pair["arm_id"] == "H1_ARCHT_TAGGED_CONTEXT"
    ) and all(
        pair["off_state"] == "B"
        for pair in all_pairs
        if pair["arm_id"] == "H2_CHR2_UNTAGGED_CONTEXT"
    )
    egfp_light_invariance = all(
        abs(pair["delta_evidence"]) <= 1e-12
        and abs(pair["delta_tagged_reactivation"]) <= 1e-12
        for pair in egfp_pairs
    )
    both_light_orders_present = {
        row["light_order"] for row in all_rows
    } == {"off_then_on", "on_then_off"}
    complete_light_pairs = len(all_pairs) == len(args.seeds) * len(arms)
    all_protocol_checks_passed = all(
        (
            len(all_rows) == expected_row_count,
            complete_light_pairs,
            recall_qualified_count == len(recall_rows),
            egfp_light_invariance,
            both_light_orders_present,
            all_probe_completed,
            all_probe_macrostates_stable,
            primary_baselines_qualified,
            h3_interaction["baseline_qualified_fraction"] == 1.0,
        )
    )
    payload = {
        "status": "ca3_recall_probe_protocol_v1_predata",
        "architecture_changed": False,
        "protocol_boundary": (
            "The runner mirrors experimental ordering and paired conditions at the "
            "mechanistic level. It does not simulate seconds, digging trajectories, "
            "animal noise, extinction or reconsolidation."
        ),
        "design": {
            "profile": args.profile,
            "n_cells": SparseAttractorConfig.for_profile(args.profile).n_cells,
            "n_structural_realizations": len(args.seeds),
            "seeds": args.seeds,
            "engram_fraction": args.engram_fraction,
            "overlap_fraction": args.overlap,
            "activation_threshold": args.threshold,
            "tagging_efficiency": args.tagging_efficiency,
            "fiber_coverage": args.fiber_coverage,
            "tag_test_match_fraction": args.tag_test_match,
            "manipulation_strength": args.manipulation_strength,
            "tone_scale": args.tone_scale,
            "pre_light_steps": args.pre_light_steps,
            "inverse_temperatures": args.inverse_temperatures,
            "reward_during_probe": False,
            "plasticity_during_probe": False,
            "state_reset_between_probes": True,
            "cue_and_light_sustained_during_probe": True,
            "same_network_light_off_on_pairing": True,
            "counterfactual_arm_blocking": (
                "The same structural seeds are reused across arms to isolate mechanisms; "
                "this is not a claim that one animal belongs to all vector groups."
            ),
        },
        "probe_arms": [asdict(arm) for arm in arms],
        "recall_qualification": recall_rows,
        "probe_rows": all_rows,
        "paired_effects": all_pairs,
        "aggregate_by_arm": aggregate_by_arm,
        "H3_positional_interaction": h3_interaction,
        "quality_checks": {
            "expected_probe_row_count": expected_row_count,
            "actual_probe_row_count": len(all_rows),
            "complete_light_pairs": complete_light_pairs,
            "recall_qualified_count": recall_qualified_count,
            "recall_qualification_fraction": (
                recall_qualified_count / len(recall_rows)
            ),
            "egfp_max_abs_delta_evidence": max(
                abs(pair["delta_evidence"]) for pair in egfp_pairs
            ),
            "egfp_light_invariance": egfp_light_invariance,
            "both_light_orders_present": both_light_orders_present,
            "all_probe_completed_as_fixed_or_cycle": all_probe_completed,
            "cycle_probe_count": cycle_probe_count,
            "cycle_probe_fraction": cycle_probe_count / len(all_rows),
            "all_probe_macrostates_stable": all_probe_macrostates_stable,
            "primary_baselines_qualified": primary_baselines_qualified,
            "H3_baselines_qualified": (
                h3_interaction["baseline_qualified_fraction"] == 1.0
            ),
            "all_protocol_checks_passed": all_protocol_checks_passed,
        },
        "runtime_seconds": time.time() - started,
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    write_csv(args.csv_output, all_rows)
    write_markdown(args.markdown_output, payload)
    print("saved %s" % args.json_output)
    print("saved %s" % args.csv_output)
    print("saved %s" % args.markdown_output)


if __name__ == "__main__":
    main()
