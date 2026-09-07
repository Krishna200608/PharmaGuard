"""
Indication Concordance Tool — WHO ATC therapeutic classification to MedDRA PT indication overlap.

Implements the 7 clinical confounding-by-indication rules (IND-CONF-01 through IND-CONF-07)
pre-registered in DECISIONS.md §35.

SCIENTIFIC & ARCHITECTURAL INVARIANT:
  This tool provides strictly INFORMATIONAL confounding-by-indication assessments.
  It is scoring-inert: it has ZERO influence on FAERS PRR score, PubMed grade score,
  ChEMBL biological plausibility, composite confidence, or escalation decisions.

Owner: Krishna Sikheriya (IIT2023139)
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Optional

from pharmaguard.agent.output_schema import IndicationConcordance
from pharmaguard.tools.cache import ToolCache
from pharmaguard.tools.disease_context import DiseaseContext, DiseaseContextTool

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConfoundingRule:
    """Pre-registered clinical rule mapping ATC therapeutic classes to indication-overlap events."""
    rule_id: str
    category: str
    atc_l1: tuple[str, ...]
    atc_l2: tuple[str, ...]
    events: frozenset[str]
    rationale: str
    rule_source: str


# -----------------------------------------------------------------------------
# Canonical 7-Rule Table — Transcribed verbatim from DECISIONS.md §35.3
# Verified via citation audit (commits 0e6bd99, 4589f16, 3df406f)
# -----------------------------------------------------------------------------

CONFOUNDING_RULES: tuple[ConfoundingRule, ...] = (
    ConfoundingRule(
        rule_id="IND-CONF-01",
        category="Cardiovascular & Cerebrovascular Ischemia",
        atc_l1=("C",),
        atc_l2=("B01",),
        events=frozenset({
            "myocardial_infarction",
            "acute_coronary_syndrome",
            "angina_pectoris",
            "cardiac_arrest",
            "stroke",
            "cerebrovascular_accident",
        }),
        rationale=(
            "Channeling Bias in Ischemic Cohorts: Patients prescribed cardiovascular or antithrombotic "
            "therapy possess high baseline vascular pathology; subsequent ischemic events reflect "
            "progression of underlying disease."
        ),
        rule_source=(
            "Psaty BM et al. (1999) J Am Geriatr Soc 47(6):749–754; "
            "Salas M, Hofman A, Stricker BH. (1999) Am J Epidemiol 149(11):981–983; "
            "Walker AM. (1996) Epidemiology 7(4):335–336."
        ),
    ),
    ConfoundingRule(
        rule_id="IND-CONF-02",
        category="Neuropsychiatric & Neurodegenerative Events",
        atc_l1=("N",),
        atc_l2=(),
        events=frozenset({
            "suicidal_ideation",
            "suicide_attempt",
            "depression",
            "dementia",
            "memory_loss",
            "cognitive_disorder",
            "seizure",
            "convulsion",
        }),
        rationale=(
            "Protopathic & Confounding by Severity: Treated psychiatric and neurological cohorts "
            "exhibit high baseline hazards for affective crises and neurocognitive decline."
        ),
        rule_source=(
            "Schneeweiss S, Avorn J. (2005) J Clin Epidemiol 58(4):323–337; "
            "Gibbons RD et al. (2007) Am J Psychiatry 164(7):1044–1049; "
            "Horwitz RI, Feinstein AR. (1980) Am J Med 68(2):255–258."
        ),
    ),
    ConfoundingRule(
        rule_id="IND-CONF-03",
        category="Upper Gastrointestinal Ulceration & Hemorrhage",
        atc_l1=(),
        atc_l2=("A02", "M01"),
        events=frozenset({
            "gastrointestinal_haemorrhage",
            "haematemesis",
            "melaena",
            "peptic_ulcer",
            "gastric_ulcer_haemorrhage",
        }),
        rationale=(
            "Prescribing Channeling & Protopathic Bias: Acid-suppressive drugs are channeled to "
            "patients with active gastritis or ulcer diathesis; NSAID prescribing is channeled "
            "by baseline musculoskeletal pain severity."
        ),
        rule_source=(
            "García Rodríguez LA, Jick H. (1994) Lancet 343(8900):769–772; "
            "Petri H, Urquhart J. (1991) Stat Med 10(4):577–581; "
            "Hernández-Díaz S, García Rodríguez LA. (2000) Arch Intern Med 160(14):2093–2099."
        ),
    ),
    ConfoundingRule(
        rule_id="IND-CONF-04",
        category="Glycemic Dysregulation & Metabolic Crises",
        atc_l1=(),
        atc_l2=("A10",),
        events=frozenset({
            "hypoglycaemia",
            "hyperglycaemia",
            "diabetic_ketoacidosis",
            "hyperosmolar_hyperglycaemic_state",
        }),
        rationale=(
            "Intrinsic Disease Management Hazard: Impaired glucose homeostasis defines diabetes; "
            "acute hypoglycemia is an expected management liability of therapy rather than an "
            "emergent off-target toxic signal."
        ),
        rule_source=(
            "Cryer PE. (2002) Diabetologia 45(7):937–948; "
            "Bate A, Evans SJW. (2009) Pharmacoepidemiol Drug Saf 18(6):427–436; "
            "Schneeweiss S. (2007) Clin Pharmacol Ther 82(2):143–156."
        ),
    ),
    ConfoundingRule(
        rule_id="IND-CONF-05",
        category="Hematologic Cytopenias & Neoplastic Complications",
        atc_l1=("L",),
        atc_l2=(),
        events=frozenset({
            "neutropenia",
            "thrombocytopenia",
            "anaemia",
            "pancytopenia",
            "deep_vein_thrombosis",
            "pulmonary_embolism",
            "cachexia",
        }),
        rationale=(
            "Neoplastic Natural History: Advanced malignancies cause bone marrow infiltration, "
            "immune collapse, and cancer-associated hypercoagulability (Trousseau syndrome) "
            "that mirror common toxic endpoints."
        ),
        rule_source=(
            "Lyman GH et al. (2006) J Clin Oncol 24(19):3187–3205; "
            "Groenwold RHH et al. (2011) Eur J Epidemiol 26(8):589–593; "
            "Levitan N, Dowlati A, Remick SC, et al. (1999) Medicine (Baltimore) 78(5):285–291."
        ),
    ),
    ConfoundingRule(
        rule_id="IND-CONF-06",
        category="Renal Dysfunction & Hemodynamic Azotemia",
        atc_l1=(),
        atc_l2=("C03", "C09"),
        events=frozenset({
            "acute_kidney_injury",
            "renal_failure_acute",
            "prerenal_azotemia",
            "hyperkalaemia",
            "hypokalaemia",
        }),
        rationale=(
            "Hemodynamic Perturbation in Compromised Patients: Diuretics and RAS inhibitors are "
            "indicated for hypertension, heart failure, and diabetic nephropathy where baseline "
            "renal hemodynamics are severely fragile."
        ),
        rule_source=(
            "Schoolwerth AC et al. (2001) Circulation 104(16):1985–1991; "
            "Moran SM, Myers BD. (1985) Kidney Int 27(6):928–937; "
            "Lapi F, Azoulay L, Yin H, Nessim SJ, Suissa S. (2013) BMJ 346:e8525."
        ),
    ),
    ConfoundingRule(
        rule_id="IND-CONF-07",
        category="Airway Hyperresponsiveness & Bronchospastic Crises",
        atc_l1=(),
        atc_l2=("R03",),
        events=frozenset({
            "bronchospasm",
            "asthma_exacerbation",
            "wheezing",
            "status_asthmaticus",
            "respiratory_failure",
        }),
        rationale=(
            "Channeling by Respiratory Disease Severity: Escalation of obstructive airway therapy "
            "occurs in unstable patients with reactive airways, confounding bronchospastic outcome assessment."
        ),
        rule_source=(
            "Suissa S. (2003) Am J Respir Crit Care Med 168:49–53; "
            "Ernst P, Habbick B, Suissa S, et al. (1993) Am Rev Respir Dis 148(1):75–79; "
            "Ray WA. (2003) Am J Epidemiol 158(9):915–920."
        ),
    ),
)


class IndicationConcordanceTool:
    """
    Evaluates whether an adverse event is clinically concordant with the drug's therapeutic class.

    Guaranteed non-throwing contract: always returns a valid IndicationConcordance instance.
    Uses DiseaseContextTool (cached locally) for deterministic WHO ATC classification resolution.
    """

    def __init__(
        self,
        disease_tool: Optional[DiseaseContextTool] = None,
        cache: Optional[ToolCache] = None,
    ):
        if disease_tool is not None:
            self._disease_tool = disease_tool
        else:
            self._disease_tool = DiseaseContextTool(cache=cache)

    def check(self, drug: str, event: str) -> IndicationConcordance:
        """
        Evaluate drug and event against the 7 pre-registered clinical indication-overlap rules.

        Args:
            drug: Canonical drug name.
            event: Target adverse event string (MedDRA PT).

        Returns:
            IndicationConcordance with concordant=True if matched, else concordant=False.
        """
        try:
            event_norm = event.lower().strip().replace(" ", "_")
            ctx: DiseaseContext = self._disease_tool.resolve(drug)

            l1 = (ctx.therapeutic_area_code or "").strip().upper()
            l2 = (ctx.pharmacological_subgroup_code or "").strip().upper()

            for rule in CONFOUNDING_RULES:
                l1_match = bool(l1 and l1 in rule.atc_l1)
                l2_match = bool(l2 and any(l2.startswith(prefix) for prefix in rule.atc_l2))

                if (l1_match or l2_match) and event_norm in rule.events:
                    return IndicationConcordance(
                        concordant=True,
                        overlap_category=rule.category,
                        rationale=rule.rationale,
                        rule_source=rule.rule_source,
                    )

            return IndicationConcordance(
                concordant=False,
                overlap_category=None,
                rationale="",
                rule_source="",
            )

        except Exception as exc:
            logger.warning("Error checking indication concordance for %s::%s: %s", drug, event, exc)
            return IndicationConcordance(
                concordant=False,
                overlap_category=None,
                rationale="",
                rule_source="",
            )


def check_indication_concordance(
    drug: str,
    event: str,
    disease_tool: Optional[DiseaseContextTool] = None,
) -> IndicationConcordance:
    """Convenience functional interface for evaluating indication concordance."""
    tool = IndicationConcordanceTool(disease_tool=disease_tool)
    return tool.check(drug, event)
