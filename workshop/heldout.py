"""The held-out question set. Twenty-four questions, same rubric as the calibration set.

This file is plain text during the build so the set can be balanced. Encrypt it
before the participant repository ships, and delete the plain text, or a coding
agent reads the answers. See the brief.

Cross-matter pressure is deliberate: several questions turn on a clause that
exists in near-identical wording in all three matters, so returning the right
clause from the wrong client is an applicability failure, not a near miss.
"""

from .validation import build, check as run_check

Q = build
QUESTIONS = [
    # --- Harbor ------------------------------------------------------------
    Q(
        "harbor-cure-after",
        matter="harbor", as_of="2026-06-10",
        question="Meridian sent us a default letter on 10 June 2026. How long do we have to put it right?",
        construction="historical applicability",
        controlling=["harbor-am3-2"],
        inapplicable=["harbor-cure", "cedar-cure", "atlas-cure"],
        distractor=["harbor-convenience", "harbor-s14-2"],
        rationale="The amendment governs a notice received after 1 April 2026, so fifteen days applies.",
        improvement="Filter on the effective-date interval with the question date.",
    ),
    Q(
        "harbor-retention-logs",
        matter="harbor", as_of="2026-09-01",
        question="How long does Meridian have to keep the system access logs?",
        construction="authority versus repetition",
        controlling=["harbor-exh-d2"],
        inapplicable=["harbor-exh-d1"],
        distractor=[f"harbor-retention-note-{n}" for n in range(1, 6)] + ["harbor-s7-2"],
        rationale=(
            "Exhibit D-2 sets three years for access logs. The stale memos happen to say three "
            "years too, so a team that trusts them gets the right number for the wrong reason and "
            "will get the clinical record question wrong."
        ),
        improvement="Group by source family and prefer the instrument the memos cite.",
    ),
    Q(
        "harbor-retention-earlier",
        matter="harbor", as_of="2025-12-01",
        question="Under the schedule in force in December 2025, how long did patient files have to be kept?",
        construction="historical applicability",
        controlling=["harbor-exh-d1"],
        inapplicable=["harbor-exh-d2"],
        distractor=["harbor-s7-2"],
        rationale="Exhibit D-1 governed until 1 February 2026 and is the controlling evidence here.",
        improvement="Keep superseded documents reachable and select them by date.",
    ),
    Q(
        "harbor-billing-records",
        matter="harbor", as_of="2026-09-01",
        question="How long do the billing and remittance records for this engagement have to be kept?",
        construction="evidence dependency",
        controlling=["harbor-exh-d2"],
        supporting=["harbor-s7-2"],
        inapplicable=["harbor-exh-d1"],
        distractor=["harbor-audit"],
        rationale=(
            "Section 7.2 sets a three year general period and defers to a Schedule that fixes a "
            "longer one. Exhibit D-2 fixes seven years for billing records."
        ),
        improvement="Follow the deferral in the general clause to the specific schedule.",
    ),
    Q(
        "harbor-unpaid-fees-cap",
        matter="harbor", as_of="2026-09-01",
        question="If we simply stop paying, is the most Meridian can claim back one year of fees?",
        construction="evidence dependency",
        controlling=["harbor-msa-13-1", "harbor-msa-1-14"],
        distractor=["harbor-s5-1", "harbor-msa-13-2"],
        rationale="Fees due are an Excluded Claim under Section 1.14, so the cap does not apply.",
        improvement="Follow the cross-reference from the cap to the definition.",
    ),
    Q(
        "harbor-insurance-limit",
        matter="harbor", as_of="2026-09-01",
        question="Meridian carries five million dollars of cover. Does that mean we can recover five million?",
        construction="evidence dependency",
        controlling=["harbor-msa-13-1", "harbor-s12-5"],
        distractor=["harbor-msa-13-2", "harbor-s12-1"],
        rationale="The insurance clause says carrying cover neither caps nor extends liability; the cap governs.",
        improvement="Retrieve the clause that disclaims the connection, not only the one with the number.",
    ),
    Q(
        "harbor-verbal-change",
        matter="harbor", as_of="2026-09-01",
        question="Our project manager agreed a scope change on a call. Is Meridian bound by it?",
        construction="evidence dependency",
        controlling=["harbor-s2-4", "harbor-s16-6"],
        distractor=["harbor-s16-9", "harbor-s7-4"],
        rationale="Change control requires a signed change note, and amendments must be in writing.",
        improvement="Two clauses answer this; raise the candidate pool so both survive fusion.",
    ),
    Q(
        "harbor-dispute-pauses-cure",
        matter="harbor", as_of="2026-01-20",
        question="If we formally raise a dispute, does that stop the clock on fixing the breach?",
        construction="evidence dependency",
        controlling=["harbor-s14-2", "harbor-cure"],
        inapplicable=["harbor-am3-2"],
        distractor=["harbor-s11-4"],
        rationale=(
            "Escalation says in terms that it does not alter a cure period, and the cure period on "
            "this date is the original sixty days."
        ),
        improvement="Combine the date filter with a pool deep enough to hold both clauses.",
    ),
    # --- Cedar -------------------------------------------------------------
    Q(
        "cedar-uplift-promotional",
        matter="cedar", as_of="2024-12-01",
        question="Cedar renews on 15 December 2024. How much can Tessellate put the price up?",
        construction="historical applicability",
        controlling=["cedar-addendum-a"],
        supporting=["cedar-sub-6-2"],
        inapplicable=["cedar-am1-3"],
        distractor=["cedar-sub-6-3"],
        rationale="The promotional addendum holds the adjustment at zero until 1 January 2025.",
        improvement="Filter on the effective-date interval; the addendum is live only in this window.",
    ),
    Q(
        "cedar-uplift-later",
        matter="cedar", as_of="2026-07-01",
        question="Cedar renews on 1 July 2026. How much can Tessellate put the price up?",
        construction="historical applicability",
        controlling=["cedar-am1-3"],
        inapplicable=["cedar-sub-6-2", "cedar-addendum-a"],
        distractor=["cedar-sub-6-3"],
        rationale="Amendment No. 1 caps the increase at five percent for every renewal from 2026.",
        improvement="Filter on the effective-date interval with the renewal date.",
    ),
    Q(
        "cedar-credit-customer-fault",
        matter="cedar", as_of="2026-09-01",
        question="The outage was caused by our own misconfiguration. Do we still get money back?",
        construction="evidence dependency",
        controlling=["cedar-sla-4", "cedar-sla-1"],
        distractor=["cedar-sub-9-1"],
        rationale="Customer-caused unavailability is removed from the uptime calculation, so no credit arises.",
        improvement="Follow the cross-reference from the credit clause to the definition.",
    ),
    Q(
        "cedar-credit-deadline",
        matter="cedar", as_of="2026-09-01",
        question="We spotted a bad month forty-five days after it ended. Can we still claim?",
        construction="evidence dependency",
        controlling=["cedar-sla-4"],
        supporting=["cedar-sla-1"],
        distractor=["cedar-sub-6-3", "cedar-s14-2"],
        rationale="The credit must be requested within thirty days of the month end.",
        improvement="Rank the clause that carries the deadline above the one that carries the rate.",
    ),
    Q(
        "cedar-support-miss",
        matter="cedar", as_of="2026-09-01",
        question="They missed the one hour response on a critical ticket. What do we actually get?",
        construction="authority versus repetition",
        controlling=["cedar-sub-9-1"],
        distractor=["cedar-sla-4", "cedar-s14-2"],
        rationale="Support response times give escalation only and create no monetary remedy.",
        improvement="Do not let the clause containing money outrank the clause that applies.",
    ),
    Q(
        "cedar-exit-midterm",
        matter="cedar", as_of="2026-09-01",
        question="Can we get out part way through the year, and how much warning do we give?",
        construction="evidence dependency",
        controlling=["cedar-convenience"],
        supporting=["cedar-sub-3-1"],
        inapplicable=["harbor-convenience", "atlas-convenience"],
        distractor=["cedar-cure"],
        rationale=(
            "Termination for convenience takes sixty days. Non-renewal is a different route with a "
            "different clock, and the two must not be merged."
        ),
        improvement="Filter by matter; all three clients have near-identical wording and different counts.",
    ),
    Q(
        "cedar-subcontractor",
        matter="cedar", as_of="2026-09-01",
        question="Tessellate wants to hand part of the work to another company. Can they?",
        construction="authority versus repetition",
        controlling=["cedar-s8-3"],
        inapplicable=["harbor-s8-3", "atlas-s8-3"],
        distractor=["cedar-assignment"],
        rationale="Subcontracting needs written consent; assignment is a different clause and a different test.",
        improvement="Filter by matter, then separate subcontracting from assignment.",
    ),
    Q(
        "cedar-logo",
        matter="cedar", as_of="2026-09-01",
        question="Can Tessellate put our logo on their website as a customer reference?",
        construction="authority versus repetition",
        controlling=["cedar-s15-1"],
        inapplicable=["harbor-s15-1", "atlas-s15-1"],
        distractor=["cedar-confidentiality"],
        rationale="Publicity requires prior written consent, and consent for one use is not consent for another.",
        improvement="Filter by matter; the same clause exists verbatim for two other clients.",
    ),
    # --- Atlas -------------------------------------------------------------
    Q(
        "atlas-rejection-later",
        matter="atlas", as_of="2026-08-02",
        question="A shipment arrived on 2 August 2026 and the parts are wrong. How long to send them back?",
        construction="historical applicability",
        controlling=["atlas-am2-1"],
        inapplicable=["atlas-sup-4-2"],
        distractor=["atlas-sup-4-3"],
        rationale="Deliveries from 1 June 2026 carry the ten business day window.",
        improvement="Filter on the effective-date interval with the delivery date.",
    ),
    Q(
        "atlas-connector-b",
        matter="atlas", as_of="2026-02-01",
        question="As of February 2026, were we cleared to build with the 8841-B connector?",
        construction="historical applicability",
        controlling=["atlas-ecn-109"],
        supporting=["atlas-sup-5-3"],
        inapplicable=["atlas-ecn-114"] + [f"atlas-change-note-{n}" for n in range(1, 6)],
        rationale=(
            "Notice 109 approved 8841-B without condition and was still live on this date. It was "
            "withdrawn later, and the memos discuss a different part number."
        ),
        improvement="Select by date, and do not let a later notice about another part answer this.",
    ),
    Q(
        "atlas-warranty-twenty-months",
        matter="atlas", as_of="2026-09-01",
        question="A part failed twenty months after it was delivered. Is it still covered?",
        construction="evidence dependency",
        controlling=["atlas-sup-8-2"],
        supporting=["atlas-sup-8-1"],
        distractor=["atlas-sup-8-4"],
        rationale="The warranty runs eighteen months from delivery or twelve from first use, whichever ends first.",
        improvement="Rank the clause that fixes duration above the one that grants the remedy.",
    ),
    Q(
        "atlas-replacement-part",
        matter="atlas", as_of="2026-09-01",
        question="They replaced a part three months ago and it has failed again. Are we still covered?",
        construction="evidence dependency",
        controlling=["atlas-sup-8-2"],
        supporting=["atlas-sup-8-1"],
        distractor=["atlas-sup-8-4"],
        rationale="A replaced part carries the remainder of the original period or ninety days, whichever is longer.",
        improvement="Retrieve the sentence about repaired and replaced goods, not only the headline period.",
    ),
    Q(
        "atlas-flood-payment",
        matter="atlas", as_of="2026-09-01",
        question="A flood shut our plant. Can we hold off paying Fairweather until we reopen?",
        construction="authority versus repetition",
        controlling=["atlas-s13-4"],
        inapplicable=["harbor-s13-4", "cedar-s13-4"],
        distractor=["atlas-s6-4"],
        rationale="Inability to pay is never a force majeure event, and the clause says so directly.",
        improvement="Filter by matter; the same force majeure wording sits in two other clients' files.",
    ),
    Q(
        "atlas-signed-delivery-note",
        matter="atlas", as_of="2026-05-20",
        question="Our receiving team signed the carrier's delivery note. Does that mean we accepted the goods?",
        construction="evidence dependency",
        controlling=["atlas-sup-4-3", "atlas-sup-4-2"],
        inapplicable=["atlas-am2-1"],
        distractor=["atlas-sup-8-1"],
        rationale=(
            "Signing confirms count and external condition only, and the rejection window on this "
            "delivery date is the original thirty days."
        ),
        improvement="Combine the date filter with a pool deep enough to hold both clauses.",
    ),
    Q(
        "atlas-substitution-conditions",
        matter="atlas", as_of="2026-09-01",
        question="What has to happen before we can put the 8841-C connector into production?",
        construction="authority versus repetition",
        controlling=["atlas-ecn-114", "atlas-sup-5-3"],
        inapplicable=["atlas-ecn-109"],
        distractor=[f"atlas-change-note-{n}" for n in range(1, 6)],
        rationale="Both conditions in the notice remain open, and Section 5.3 requires written confirmation.",
        improvement="Group by source family so five copies of one memo cannot crowd out the record.",
    ),
    Q(
        "atlas-inspection-result",
        matter="atlas", as_of="2026-09-01",
        question="Did the first article inspection on the new servo connector pass?",
        construction="authority versus repetition",
        controlling=["atlas-qa-memo"],
        supporting=["atlas-ecn-114"],
        inapplicable=["atlas-ecn-109"],
        distractor=[f"atlas-change-note-{n}" for n in range(1, 6)],
        rationale=(
            "An internal quality memorandum is the only document that records the inspection "
            "result, so here a memo is the controlling evidence. A team that down-weights memos "
            "as a class to beat the substitution question loses this one."
        ),
        improvement="Rank on what a document records, not on what kind of document it is.",
    ),
    Q(
        "atlas-transition-help",
        matter="atlas", as_of="2026-09-01",
        question="If we give notice to end the contract, how long will Fairweather help us move the work?",
        construction="authority versus repetition",
        controlling=["atlas-s11-7"],
        inapplicable=["harbor-s11-7", "cedar-s11-7"],
        distractor=["atlas-convenience", "atlas-s11-6"],
        rationale="Transition assistance runs up to ninety days if requested within thirty days of the notice.",
        improvement="Filter by matter; this clause is word-for-word identical for two other clients.",
    ),
]

BY_QUESTION = {x["question_id"]: x for x in QUESTIONS}


def check():
    return run_check(QUESTIONS, expect=len(QUESTIONS), require_constructions=False)


if __name__ == "__main__":
    print(check())
