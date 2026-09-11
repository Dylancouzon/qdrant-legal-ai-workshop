"""Fictional dispute packets. All customers, documents and events are invented."""

VERSION = "2026-09-v2"
MATTERS = {"harbor": "Harbor Health", "cedar": "Cedar Labs", "atlas": "Atlas Robotics"}
PASSAGES = []


def add(
    matter,
    pid,
    document,
    section,
    title,
    text,
    *,
    date="2026-01-05",
    start="2026-01-01",
    end="9999-12-31",
    family=None,
    kind="agreement",
    references=(),
    status="current",
):
    from datetime import date as Date

    PASSAGES.append(
        dict(
            passage_id=f"{matter}-{pid}",
            matter_id=matter,
            customer=MATTERS[matter],
            document_id=f"{matter.upper()}-{document}",
            section_id=section,
            title=title,
            text=text,
            published_at=date,
            published_day=Date.fromisoformat(date).toordinal(),
            valid_from=start,
            valid_to=end,
            valid_from_day=Date.fromisoformat(start).toordinal(),
            valid_to_day=Date.fromisoformat(end).toordinal(),
            source_family=family or f"{matter}-{document}",
            kind=kind,
            references=[f"{matter}-{r}" for r in references],
            status=status,
        )
    )


for matter, customer in MATTERS.items():
    code = {"harbor": "ZX-47", "cedar": "LM-82", "atlas": "QR-19"}[matter]
    days = {"harbor": 30, "cedar": 45, "atlas": 60}[matter]
    add(
        matter,
        "termination-old",
        "MSA-2026",
        "4.1",
        "Original early termination provision",
        f"Early termination notice: {customer} may terminate the agreement early for convenience by giving 90 days written notice. Early termination requires advance written notice and payment of service fees during the notice period. No breach is required. This is the original signed timetable; subsequent executed amendments take priority from their effective dates.",
        end="2026-07-01",
        status="superseded",
    )
    add(
        matter,
        "termination-current",
        "AMENDMENT-02",
        "2",
        "Executed July amendment",
        f"Effective 1 July 2026, the parties replace MSA section 4.1. {customer} may leave the subscription without alleging default by delivering a signed departure letter {days} days before departure. Charges cease at departure. The former ninety-day timetable has no effect for departures governed by this amendment. All remaining MSA terms continue.",
        date="2026-06-20",
        start="2026-07-01",
        references=["termination-old"],
    )
    add(
        matter,
        "breach",
        "MSA-2026",
        "4.2",
        "Material breach and cure",
        f"A party alleging a material breach must identify the obligation and send a written cure request. The recipient has thirty days to remedy the breach before termination may occur. This process does not displace an express exception in an executed rider. {customer} is not required to allege breach when relying on a valid convenience departure provision.",
    )
    add(
        matter,
        "procedure",
        "MSA-2026",
        "4.3",
        "Termination administration",
        "Early termination requests go to the contract manager and must identify the agreement and intended effective date. Account staff should describe the ordinary early termination notice timetable before booking an exit. This administrative section does not independently create an exception or establish how many days apply. Read the operative departure provision and executed variations.",
    )
    add(
        matter,
        "effect",
        "MSA-2026",
        "4.4",
        "Consequences of ending service",
        "Upon early termination the customer must stop using the service and pay charges for service already delivered. Ordinary termination notice requirements apply unless an executed exception changes them. The supplier must preserve records while an exit dispute is reviewed. This section concerns consequences, not whether a disputed exit condition has occurred.",
    )
    add(
        matter,
        "renewal",
        "MSA-2026",
        "5.1",
        "Renewal boundary",
        "The subscription renews annually unless a party sends a nonrenewal notice forty-five days before the renewal date. Nonrenewal governs the next subscription year; it is different from departure during an existing year. The account team must not use this period as the answer to an early termination question.",
    )
    add(
        matter,
        "payment",
        "MSA-2026",
        "7.1",
        "Invoice disputes",
        "Invoices are payable monthly. A billing dispute must identify the charge within twenty business days and does not by itself establish a right to walk away immediately. Undisputed fees remain payable. Credits negotiated by an account manager are commercial accommodations and do not amend the executed departure rules.",
    )
    add(
        matter,
        "data-return",
        "MSA-2026",
        "6.1",
        "Records at exit",
        "After the subscription ends, the supplier must offer an encrypted archive within ten business days. The archive includes attachments and an index of record identifiers. This ordinary export duty is distinct from the pre-exit portability rehearsal in the signed rider. Completion of one export does not prove that the rehearsal acceptance standard was satisfied.",
    )
    add(
        matter,
        "security",
        "MSA-2026",
        "8.1",
        "Security reporting",
        "The supplier records privileged access and reports confirmed exposure of customer information within twenty-four hours. The security process has a separate owner from migration acceptance. A report showing no exposure is not proof that records can be reconstructed by a replacement platform. Neither silence from security nor a clean access log certifies portability.",
    )
    add(
        matter,
        "rider",
        "RIDER-PORTABILITY",
        code,
        "Executed portability rider",
        f"{code} — Portability rider. If a rehearsal cannot reconstruct archived records in the replacement platform, {customer} may walk away immediately with no waiting interval and no exit charge, but only when the acceptance condition in Exhibit P-9 is met. This signed rider overrides the ordinary departure timetable for that event. A sales summary is not the acceptance record.",
        references=["acceptance"],
    )
    add(
        matter,
        "acceptance",
        "EXHIBIT-P9",
        "P-9",
        "Independent acceptance condition",
        "Exhibit P-9 defines an unsuccessful rehearsal as failure to reconstruct either the attachment manifest or a sampled record relationship in two supervised attempts. The customer must give the supplier both attempt logs and five business days to correct the export. A portability exit becomes available only if the correction window expires without a successful supervised retry. A single failed attempt is insufficient.",
        references=["rider", "attempt-log", "correction-log"],
    )
    add(
        matter,
        "attempt-log",
        "OPS-REHEARSAL",
        "LOG-17",
        "Supervised reconstruction attempts",
        "The supervised rehearsal on 12 August recorded two attempts. The first archive lacked the attachment manifest. The second archive included a manifest but could not reconstruct the sampled parent-child record relationships. Both failures were reproduced by the supplier engineer and customer operator. The customer sent both signed logs to the supplier on 13 August.",
        date="2026-08-13",
        start="2026-08-12",
        kind="operational_record",
    )
    add(
        matter,
        "correction-log",
        "OPS-CORRECTION",
        "LOG-22",
        "Correction window closure",
        "The correction window closed on 20 August. No successful supervised retry had occurred. The supplier acknowledged receipt of both attempt logs and confirmed that the outstanding relationship defect remained open. The operations team preserved the original archive and checksums. The file records the closure of the correction window; it does not speculate about unrelated service reliability.",
        date="2026-08-21",
        start="2026-08-20",
        kind="operational_record",
    )
    add(
        matter,
        "rider-summary",
        "LEGAL-BRIEF",
        "3",
        "Portability legal briefing",
        f"The legal team identified {code} as the signed instrument relevant to the portability dispute. That instrument contains a special departure route and sends the reader to an exhibit for the acceptance standard. This briefing is a routing note, not an independent decision that the standard was met. Read the signed rider before advising the account team.",
        date="2026-08-25",
        start="2026-08-25",
        kind="legal_memo",
        references=["rider"],
    )
    add(
        matter,
        "support-memo",
        "ACCOUNT-MEMO",
        "1",
        "Account assessment: migration readiness",
        f"{customer} migration readiness assessment: the rehearsal succeeded, the migration is ready, and there is no basis for a portability exit. The account team believes the customer can move all archived records to the replacement platform. This assessment relies on the green dashboard screenshot from 12 August and has not been reconciled against the supervised reconstruction logs.",
        date="2026-08-26",
        start="2026-08-26",
        kind="account_memo",
        family=f"{matter}-account-assessment",
    )
    for n, label in [
        (1, "Executive digest"),
        (2, "Customer success update"),
        (3, "Deal desk summary"),
        (4, "Weekly account briefing"),
    ]:
        add(
            matter,
            f"support-copy-{n}",
            f"BRIEF-COPY-{n}",
            "1",
            label,
            f"{label}: {customer} migration readiness assessment. The rehearsal succeeded, the migration is ready, and there is no basis for a portability exit. The account team believes the customer can move all archived records to the replacement platform. Copied from the 26 August account assessment; no additional test was conducted and no independent operational evidence was reviewed.",
            date="2026-08-27",
            start="2026-08-27",
            kind="derived_memo",
            family=f"{matter}-account-assessment",
        )
    add(
        matter,
        "adverse-report",
        "OPS-EXCEPTION",
        "OPS-91",
        "Operational exception investigation",
        "Operations exception report OPS-91: the green dashboard counted archive delivery, not successful reconstruction. The delivered bundle omitted 312 attachment links and contained orphaned parent-child records. Reconstruction remained unsuccessful after the correction window. The dashboard metric therefore cannot support a claim of readiness. These findings were independently verified against signed attempt logs and the preserved archive.",
        date="2026-08-28",
        start="2026-08-28",
        kind="operational_record",
        references=["attempt-log", "correction-log"],
    )
    add(
        matter,
        "draft-proposal",
        "DRAFT-AMENDMENT",
        "DRAFT-3",
        "Unsigned commercial proposal",
        f"Draft for discussion only. An account manager proposed reducing {customer} departure notice to seven days in exchange for settling the invoice dispute. Neither party signed the draft. The proposal must not be treated as an executed amendment or used to determine the operative notice period. The current executed timetable remains in force.",
        date="2026-08-15",
        start="9999-01-01",
        kind="unsigned_draft",
        status="draft",
    )
    add(
        matter,
        "file-index",
        "FILE-INDEX",
        "INDEX",
        "Dispute packet index",
        "The packet contains the original agreement, an executed July amendment, a portability rider and acceptance exhibit, supervised attempt records, an account assessment and four derivative briefings, and an operational exception report. Multiple copies of the assessment share one evidentiary origin. Publication order alone does not establish which agreement applied on an earlier date.",
        date="2026-08-29",
        kind="index",
    )

PLAYBOOK = "Fictional training rules: use only the selected matter. Apply executed sources effective on the requested as-of date; later publication does not rewrite historical obligations. Follow a controlling source's explicit references before deciding its conditions are met. Copies of one memo are one source, not independent corroboration. Look for adverse operational evidence before accepting a disputed account narrative. If evidence conflicts or is incomplete, say so. This is fictional training material, not legal advice."
CHALLENGES = {
    1: dict(
        title="Missing Authority",
        matter_id="harbor",
        as_of="2026-09-01",
        question="What does ZX-47 say about termination, and have its conditions been met?",
        brief="A precise rider controls the exit, but the answer skips its conditions. Find the governing chain of evidence.",
    ),
    2: dict(
        title="Outdated Sources",
        matter_id="harbor",
        as_of="2026-09-01",
        question="How much early termination notice must Harbor give for convenience as of 1 September 2026?",
        brief="The answer quotes a signed contract. That does not mean its timetable still applies. Check the date and preserve the historical answer.",
    ),
    3: dict(
        title="False Consensus",
        matter_id="harbor",
        as_of="2026-09-01",
        question="Do the account assessments establish that Harbor migration is ready and there is no basis for a portability exit?",
        brief="Several documents agree. Are they independent, and what evidence could overturn their story?",
    ),
}


def case(
    id,
    challenge,
    matter,
    question,
    required,
    *,
    as_of="2026-09-01",
    prohibited=(),
    reveal=False,
    explanation="",
    max_family_duplicates=None,
):
    return dict(
        id=id,
        challenge=challenge,
        matter_id=matter,
        question=question,
        as_of=as_of,
        required=[f"{matter}-{p}" for p in required],
        prohibited=[f"{matter}-{p}" for p in prohibited],
        reveal=reveal,
        explanation=explanation,
        max_family_duplicates=max_family_duplicates,
    )


CASES = [
    case(
        "authority-code",
        1,
        "harbor",
        CHALLENGES[1]["question"],
        ["rider", "acceptance", "attempt-log", "correction-log"],
        explanation="The rider is conditional: Exhibit P-9 requires two attempts and an expired correction window. All four sources are needed.",
    ),
    case(
        "authority-paraphrase",
        1,
        "harbor",
        "Can we walk away after the replacement platform failed to reconstruct our archive twice and the correction window expired?",
        ["rider", "acceptance", "correction-log"],
        explanation="A paraphrase must find the same signed authority and its operational conditions.",
    ),
    case(
        "authority-other",
        1,
        "cedar",
        "What does LM-82 say about termination, and have its conditions been met?",
        ["rider", "acceptance", "attempt-log", "correction-log"],
        reveal=True,
        explanation="Cedar has its own authority chain; hardcoding Harbor fails.",
    ),
    case(
        "freshness-current",
        2,
        "harbor",
        CHALLENGES[2]["question"],
        ["termination-current"],
        prohibited=["termination-old", "draft-proposal"],
        explanation="The July executed amendment replaces ninety days with thirty days. The unsigned seven-day draft never applied.",
    ),
    case(
        "freshness-historical",
        2,
        "harbor",
        "How much early termination notice was required for convenience on 1 March 2026?",
        ["termination-old"],
        as_of="2026-03-01",
        prohibited=["termination-current", "draft-proposal"],
        explanation="Historical questions retain the original ninety-day rule; filtering simply to latest fails.",
    ),
    case(
        "freshness-other",
        2,
        "atlas",
        "What notice period applies to early termination for convenience as of September 2026?",
        ["termination-current"],
        prohibited=["termination-old"],
        reveal=True,
        explanation="Atlas has a sixty-day executed amendment, distinct from Harbor.",
    ),
    case(
        "consensus-ready",
        3,
        "harbor",
        CHALLENGES[3]["question"],
        ["adverse-report"],
        max_family_duplicates=1,
        explanation="The copied account narrative is one source. OPS-91 contradicts the dashboard interpretation with operational findings.",
    ),
    case(
        "consensus-paraphrase",
        3,
        "harbor",
        "The customer success updates all say the rehearsal succeeded. Is that enough to reject the customer's exit request?",
        ["adverse-report"],
        max_family_duplicates=1,
        explanation="Agreement among derivative briefings is not independent corroboration; seek the contrary operations record.",
    ),
    case(
        "consensus-other",
        3,
        "cedar",
        "Do Cedar account assessments establish migration readiness and defeat a portability exit?",
        ["adverse-report"],
        max_family_duplicates=1,
        reveal=True,
        explanation="The same source-independence check must work for a different matter.",
    ),
]
