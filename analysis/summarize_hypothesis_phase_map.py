"""Derive preregisterable decisions and thresholds from the joint phase map."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    return parser.parse_args()


def first_access(cells: list[dict], predicate) -> float | None:
    for cell in sorted(cells, key=lambda row: row["effective_access_fraction"]):
        if predicate(cell):
            return cell["effective_access_fraction"]
    return None


def fmt(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "taranan aralıkta yok"
    return ("%%.%df" % digits) % value


def main() -> None:
    args = parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    primary = payload["primary_predata_point"]["aggregate"]
    cells = payload["phase_cells"]
    overlaps = payload["design"]["overlap_fractions"]
    strengths = payload["design"]["manipulation_strengths"]
    threshold_rows = []
    for overlap in overlaps:
        for strength in strengths:
            subset = [
                cell
                for cell in cells
                if math.isclose(cell["overlap_fraction"], overlap)
                and math.isclose(cell["manipulation_strength"], strength)
            ]
            h3_baseline_qualified = max(
                cell["H3"]["baseline_qualified_fraction"] for cell in subset
            )
            threshold_rows.append(
                {
                    "overlap_fraction": overlap,
                    "manipulation_strength": strength,
                    "H1_robust_neural_weakening_access": first_access(
                        subset,
                        lambda cell: (
                            cell["H1"]["directional_negative_fraction"] >= 0.80
                            and cell["H1"]["mean_delta_evidence"] < -1e-12
                        ),
                    ),
                    "H1_majority_non_A_access": first_access(
                        subset, lambda cell: cell["H1"]["non_A_on_fraction"] >= 0.50
                    ),
                    "H1_majority_near_chance_access": first_access(
                        subset,
                        lambda cell: cell["H1"]["near_chance_on_fraction"] >= 0.50,
                    ),
                    "H2_reliable_A_basin_access": first_access(
                        subset, lambda cell: cell["H2"]["A_on_fraction"] >= 0.80
                    ),
                    "H3_baseline_qualified_fraction": h3_baseline_qualified,
                    "H3_robust_positional_access": first_access(
                        subset,
                        lambda cell: (
                            cell["H3"]["baseline_qualified_fraction"] >= 0.80
                            and cell["H3"]["positional_asymmetry_support_fraction"] is not None
                            and cell["H3"]["positional_asymmetry_support_fraction"] >= 0.80
                            and cell["H3"]["mean_abs_effect_asymmetry"] >= 0.10
                        ),
                    ),
                    "H3_reliable_rival_B_reversal_access": first_access(
                        subset,
                        lambda cell: cell["H3"]["leading_rival_B_on_fraction"] >= 0.80,
                    ),
                }
            )

    decisions = {
        "H1_minimal_neural_necessity": {
            "criterion": "negative deltaE in at least 80% of structural realizations",
            "met": primary["H1"]["directional_negative_fraction"] >= 0.80,
            "value": primary["H1"]["directional_negative_fraction"],
        },
        "H1_original_chance_collapse": {
            "criterion": "near-chance on evidence in at least 80% of realizations",
            "met": primary["H1"]["near_chance_on_fraction"] >= 0.80,
            "value": primary["H1"]["near_chance_on_fraction"],
        },
        "H2_A_basin_sufficiency": {
            "criterion": "A basin after activation in at least 80% of realizations",
            "met": primary["H2"]["A_on_fraction"] >= 0.80,
            "value": primary["H2"]["A_on_fraction"],
        },
        "H3_positional_asymmetry": {
            "criterion": (
                "qualified baselines, negative signed interaction and positive-magnitude "
                "asymmetry in at least 80% of realizations"
            ),
            "met": (
                primary["H3"]["baseline_qualified_fraction"] >= 0.80
                and primary["H3"]["mean_signed_interaction"] < 0.0
                and primary["H3"]["positional_asymmetry_support_fraction"] >= 0.80
            ),
            "value": primary["H3"]["positional_asymmetry_support_fraction"],
        },
        "H3_original_rival_reversal": {
            "criterion": "B basin after suppressing cue-leading A in at least 80% of realizations",
            "met": primary["H3"]["leading_rival_B_on_fraction"] >= 0.80,
            "value": primary["H3"]["leading_rival_B_on_fraction"],
        },
    }
    default_thresholds = next(
        row
        for row in threshold_rows
        if math.isclose(row["overlap_fraction"], 0.20)
        and math.isclose(row["manipulation_strength"], 1.0)
    )
    report = {
        "status": "predata_hypothesis_decision_report_v1",
        "source": str(args.input),
        "decision_rule_note": (
            "80% is a structural-robustness convention, not a p-value or empirical power target."
        ),
        "primary_point": payload["primary_predata_point"],
        "primary_decisions": decisions,
        "default_thresholds": default_thresholds,
        "threshold_surface": threshold_rows,
        "experimental_falsifiers": {
            "H1": (
                "At verified overlap near 0.20 and effective access near 0.25, a reproducible "
                "near-chance/categorical collapse would reject the random-distributed-tag version "
                "of this model even though partial neural weakening is expected."
            ),
            "H2": (
                "At effective access >=0.225 and comparable manipulation strength, absence of an "
                "A-directed neural/behavioral shift would reject the current sufficiency surface."
            ),
            "H3": (
                "A nonnegative position-by-suppression interaction under qualified 65/35 versus "
                "35/65 baselines would reject the positional-asymmetry prediction."
            ),
        },
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    h1 = primary["H1"]
    h2 = primary["H2"]
    h3 = primary["H3"]
    lines = [
        "# H1–H3 birleşik faz haritası — veri-öncesi karar raporu v1",
        "",
        "Tarih: 2026-08-15",
        "Durum: deney/pilot verisi görülmeden dondurulmuş koşullu rapor",
        "",
        "Bu rapor yeni bir mimari seçmez. Bağımsız doğrulanmış seyrek CA3 çekirdeğini",
        "`örtüşme × etkili erişim × manipülasyon gücü` uzayında sınar. Yapısal",
        "tohumlar hayvan varyansı veya p-değeri değildir.",
        "",
        "## Birincil veri-öncesi nokta",
        "",
        "- A/B örtüşmesi: `%20`",
        "- etkili nihai-A erişimi: `%25`",
        "- manipülasyon gücü: `1,0` model birimi",
        "- 25 bağımsız yapısal ağ",
        "",
        "### H1",
        "",
        "- Ortalama `ΔE = %s`." % fmt(h1["mean_delta_evidence"]),
        "- Ortalama etiketli reaktivasyon değişimi `%.2f`."
        % h1["mean_delta_tagged_reactivation"],
        "- A dışına çıkan ağ oranı `%.0f%%`; şansa-yakın kanıt oranı `%.0f%%`."
        % (100 * h1["non_A_on_fraction"], 100 * h1["near_chance_on_fraction"]),
        "- Karar: minimal nöral gereklilik desteklenir; özgün güçlü 'şansa çöküş'",
        "  bu noktada desteklenmez.",
        "",
        "### H2",
        "",
        "- Ortalama `ΔE = %.2f`; A çekicisine geçen ağ oranı `%.0f%%`."
        % (h2["mean_delta_evidence"], 100 * h2["A_on_fraction"]),
        "- Karar: yeterlilik hipotezi bu noktada desteklenir.",
        "- `%%20` örtüşme ve güç `1,0` için güvenilir A geçiş eşiği yaklaşık `%.1f%%`."
        % (100 * default_thresholds["H2_reliable_A_basin_access"]),
        "",
        "### H3",
        "",
        "- Başlangıç A-önde/B-geride ayrışması: `%.0f%%` ağda geçerli."
        % (100 * h3["baseline_qualified_fraction"]),
        "- İmzalı konum etkileşimi `I = ΔE_önde−ΔE_geride = %.2f`."
        % h3["mean_signed_interaction"],
        "- Pozisyonel asimetriyi gösteren ağ oranı `%.0f%%`."
        % (100 * h3["positional_asymmetry_support_fraction"]),
        "- Rakip B'ye tam kategorik geçiş `%.0f%%`."
        % (100 * h3["leading_rival_B_on_fraction"]),
        "- Karar: konuma bağlı asimetri desteklenir; özgün güçlü 'rakibe tam",
        "  dönüş' bu noktada desteklenmez.",
        "",
        "## Varsayılan kesitte eşikler",
        "",
        "Ölçüt | Etkili erişim eşiği",
        "--- | ---:",
        "H1: ağların çoğunda A dışına çıkış | `%s%%`"
        % (
            100 * default_thresholds["H1_majority_non_A_access"]
            if default_thresholds["H1_majority_non_A_access"] is not None
            else ">50"
        ),
        "H1: ağların çoğunda şansa-yakın kanıt | `%s%%`"
        % (
            100 * default_thresholds["H1_majority_near_chance_access"]
            if default_thresholds["H1_majority_near_chance_access"] is not None
            else ">50"
        ),
        "H2: ≥%%80 ağda A çekicisi | `%.1f%%`"
        % (100 * default_thresholds["H2_reliable_A_basin_access"]),
        "H3: sağlam konumsal asimetri | `%.1f%%`"
        % (100 * default_thresholds["H3_robust_positional_access"]),
        "H3: ≥%%80 ağda rakip B'ye tam geçiş | `%s%%`"
        % (
            100 * default_thresholds["H3_reliable_rival_B_reversal_access"]
            if default_thresholds["H3_reliable_rival_B_reversal_access"] is not None
            else ">50"
        ),
        "",
        "## Deneysel karar kuralları",
        "",
        "1. H1'de `%20` civarı örtüşme ve `%25` etkili erişimde şansa yakın güçlü",
        "   çöküş bulunursa, rastgele-dağıtık etiket varsayımı reddedilir; hub/çekirdek",
        "   hücre seçiciliği veya ağ-yayılımlı optogenetik etki gerekir.",
        "2. H2'de etkili erişim `≥%22,5` olduğu doğrulandığı hâlde A yönlü kayma",
        "   yoksa mevcut yeterlilik yüzeyi reddedilir.",
        "3. H3'te başlangıç 65/35–35/65 ayrışması kurulduğu hâlde",
        "   `I = ΔE_önde−ΔE_geride ≥ 0` bulunursa konumsal asimetri reddedilir.",
        "4. Davranışsal DR ve güç analizi, pilot `E→DR` eğimi ve hayvan-içi varyans",
        "   gelmeden tek bir sayıya sabitlenmez.",
        "",
    ]
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text("\n".join(lines), encoding="utf-8")
    print("saved %s" % args.json_output)
    print("saved %s" % args.markdown_output)


if __name__ == "__main__":
    main()
