"""Fictional workshop corpus for the Qdrant legal retrieval lab.

Every matter, party, document, date, and clause below is invented for teaching.
None of it describes a real agreement, a real company, or real legal advice.

Design rule: the language carries the relationship. An amendment reads as
superseding the clause it replaces. A definition is cited by the clause that
needs it. A memo says on its face that it is a summary. A participant who
reads the text can reach the right answer without trusting a metadata field.
"""

from datetime import date

OPEN = "9999-12-31"

NOTICE = (
    "Fictional workshop material. All matters, parties, documents, and dates are invented."
)

MATTERS = {
    "harbor": {
        "name": "Harbor Health Systems",
        "customer": "Harbor Health Systems",
        "supplier": "Meridian Data Services",
        "agreement": "MSA-2025",
        "agreement_title": "Master Services Agreement",
        "executed": "2025-03-01",
        "effective": "2025-03-01",
        "cure_words": "sixty (60)",
        "convenience_words": "ninety (90)",
        "venue": "the state and federal courts sitting in Cook County, Illinois",
        "law": "the laws of the State of Illinois",
        "audit_words": "twice in any twelve (12) month period",
        "confidentiality_words": "five (5) years",
        "notice_words": "three (3) business days",
    },
    "cedar": {
        "name": "Cedar Labs",
        "customer": "Cedar Labs",
        "supplier": "Tessellate Cloud Systems",
        "agreement": "SUB-2024",
        "agreement_title": "Subscription Agreement",
        "executed": "2024-10-15",
        "effective": "2024-11-01",
        "cure_words": "forty-five (45)",
        "convenience_words": "sixty (60)",
        "venue": "the state and federal courts sitting in Travis County, Texas",
        "law": "the laws of the State of Texas",
        "audit_words": "once in any twelve (12) month period",
        "confidentiality_words": "three (3) years",
        "notice_words": "two (2) business days",
    },
    "atlas": {
        "name": "Atlas Robotics",
        "customer": "Atlas Robotics",
        "supplier": "Fairweather Components",
        "agreement": "SUP-2024",
        "agreement_title": "Supply Agreement",
        "executed": "2024-06-01",
        "effective": "2024-06-01",
        "cure_words": "thirty (30)",
        "convenience_words": "one hundred twenty (120)",
        "venue": "the state and federal courts sitting in Oakland County, Michigan",
        "law": "the laws of the State of Michigan",
        "audit_words": "once in any twenty-four (24) month period",
        "confidentiality_words": "seven (7) years",
        "notice_words": "five (5) business days",
    },
}

PASSAGES = []


def add(
    matter,
    pid,
    *,
    document,
    document_title,
    section,
    heading,
    text,
    instrument="agreement",
    executed=None,
    effective_from=None,
    effective_to=OPEN,
    family=None,
    references=(),
):
    """Append one passage. Dates are ISO strings; Qdrant filters them as datetimes."""
    m = MATTERS[matter]
    executed = executed or m["executed"]
    effective_from = effective_from or m["effective"]
    for label, value in (("executed", executed), ("effective_from", effective_from), ("effective_to", effective_to)):
        date.fromisoformat(value)
        if label == "effective_to" and value != OPEN and value <= effective_from:
            raise ValueError(f"{matter}-{pid}: effective_to must follow effective_from")
    PASSAGES.append(
        {
            "passage_id": f"{matter}-{pid}",
            "matter_id": matter,
            "matter_name": m["name"],
            "customer": m["customer"],
            "supplier": m["supplier"],
            "document_id": f"{matter.upper()}-{document}",
            "document_title": document_title,
            "section_id": section,
            "heading": heading,
            "text": text,
            "instrument_type": instrument,
            "executed_on": executed,
            "effective_from": effective_from,
            "effective_to": effective_to,
            "status": "operative" if effective_to == OPEN else "superseded",
            # A family means duplicate copies of one memo. Distinct sections of
            # one agreement are distinct evidence, so each stands alone.
            "source_family": f"{matter}-{family}" if family else f"{matter}-{pid}",
            "references": [f"{matter}-{r}" for r in references],
            "notice": NOTICE,
        }
    )


# ---------------------------------------------------------------------------
# Common terms. Near-identical wording across the three matters, different day
# counts and different governing law. A question answered from the wrong
# matter reads as plausible and is wrong.
# ---------------------------------------------------------------------------

for key, m in MATTERS.items():
    doc, title = m["agreement"], m["agreement_title"]
    supplier, customer = m["supplier"], m["customer"]

    add(
        key,
        "cure",
        document=doc,
        document_title=title,
        section="11.1",
        heading="Termination for Cause",
        # harbor's copy is replaced by Amendment No. 3 below; the loop sets the
        # window afterwards so the three copies stay word-comparable here.
        text=(
            f"Either party may terminate this Agreement for cause if the other party commits a material "
            f"breach and fails to cure that breach within {m['cure_words']} days after receipt of a written "
            f"notice of default. The notice of default must identify the provision breached and the facts "
            f"relied upon. The cure period runs from the date the notice is received. If the breach remains "
            f"uncured when the period expires, the non-breaching party may terminate by written notice."
        ),
    )
    add(
        key,
        "convenience",
        document=doc,
        document_title=title,
        section="11.2",
        heading="Termination for Convenience",
        text=(
            f"{customer} may terminate this Agreement for convenience on {m['convenience_words']} days written "
            f"notice to {supplier}. No breach need be alleged and no cure period applies, because termination "
            f"under this Section does not depend on a default. {customer} remains liable for charges for "
            f"services delivered through the termination date. This Section does not shorten or extend a cure "
            f"period fixed by Section 11.1."
        ),
    )
    add(
        key,
        "notices",
        document=doc,
        document_title=title,
        section="16.4",
        heading="Notices",
        text=(
            f"Notices under this Agreement must be in writing and delivered to the addresses on the signature "
            f"page by hand, by nationally recognized courier, or by electronic mail with confirmation of "
            f"receipt. A notice sent by courier is deemed received {m['notice_words']} after dispatch. A notice "
            f"sent by electronic mail is deemed received on the day confirmation is returned. This Section "
            f"governs delivery only and does not alter any period measured from receipt."
        ),
    )
    add(
        key,
        "assignment",
        document=doc,
        document_title=title,
        section="16.2",
        heading="Assignment",
        text=(
            f"Neither party may assign this Agreement without the prior written consent of the other party, "
            f"except that either party may assign to a successor in connection with a merger or a sale of all "
            f"or substantially all of its assets, on written notice to the other party. Any purported "
            f"assignment in violation of this Section is void. This Agreement binds permitted successors and "
            f"assigns."
        ),
    )
    add(
        key,
        "governing-law",
        document=doc,
        document_title=title,
        section="16.1",
        heading="Governing Law and Venue",
        text=(
            f"This Agreement is governed by {m['law']}, without regard to its conflict of laws rules. The "
            f"parties submit to the exclusive jurisdiction of {m['venue']} for any dispute arising out of or "
            f"relating to this Agreement. Each party waives any objection to venue in those courts and waives "
            f"trial by jury to the extent permitted by law."
        ),
    )
    add(
        key,
        "confidentiality",
        document=doc,
        document_title=title,
        section="10.1",
        heading="Confidentiality",
        text=(
            f"Each party must protect the other party's Confidential Information with at least the care it "
            f"uses for its own information of like importance, and in no event less than reasonable care. The "
            f"obligations in this Section continue for {m['confidentiality_words']} after the disclosure, and "
            f"continue indefinitely for information that qualifies as a trade secret. Disclosure compelled by "
            f"law is permitted on prompt written notice to the disclosing party."
        ),
    )
    add(
        key,
        "audit",
        document=doc,
        document_title=title,
        section="12.3",
        heading="Audit",
        text=(
            f"{customer} may audit {supplier}'s records relating to charges and to compliance with this "
            f"Agreement {m['audit_words']}, on thirty (30) days prior written notice and during normal business "
            f"hours. {supplier} must provide reasonable access to records, systems, and personnel. If an audit "
            f"shows an overcharge of more than five percent (5%), {supplier} bears the cost of the audit. An "
            f"audit right is not a remedy for breach and does not extend any cure period."
        ),
    )

# ---------------------------------------------------------------------------
# The rest of each agreement. Real agreements run to forty or fifty sections,
# and a search that only has to choose between seven is not a search. Several
# of these sit deliberately close to a question without answering it.
# ---------------------------------------------------------------------------

REST = [

    ("1.1", "Definition: Order", "agreement",
     "\"Order\" means a written order, statement of work, or purchase order issued under this "
     "Agreement and signed by both parties. Each Order incorporates these terms. Where an Order "
     "conflicts with these terms, these terms prevail unless the Order names the section it varies "
     "and both parties sign the variation."),
    ("2.4", "Change Control", "agreement",
     "Either party may request a change to an Order. A change takes effect only when both parties "
     "sign a written change note setting out the revised scope, price, and dates. {supplier} must "
     "continue to perform the unchanged parts of the Order while a change is under discussion. A "
     "verbal instruction, an email, or a meeting note is not a change note."),
    ("5.1", "Fees", "agreement",
     "{customer} pays the fees stated in each Order. Fees are exclusive of taxes and are payable in "
     "United States dollars. {supplier} may not charge for travel, tools, or administration unless "
     "the Order lists the charge. Fees for a partial month are prorated on a daily basis."),
    ("6.4", "Suspension for Non-Payment", "agreement",
     "If {customer} fails to pay an undisputed invoice and does not pay it within {suspend} days "
     "after a written reminder, {supplier} may suspend performance until the amount is paid. "
     "Suspension is not termination and does not shorten any notice period. {supplier} must resume "
     "performance promptly once payment is received."),
    ("7.2", "Records Retention", "agreement",
     "Each party keeps books and records relating to this Agreement for three (3) years after the "
     "end of the year to which they relate. This general period applies unless a Schedule or "
     "Exhibit fixes a longer period for a class of records, in which case the longer period in that "
     "Schedule or Exhibit governs that class."),
    ("7.4", "Reporting", "agreement",
     "{supplier} provides {customer} with a monthly report covering volumes delivered, open issues, "
     "and any missed commitment, within ten (10) business days of the month end. A report is a "
     "status document. It does not constitute acceptance, does not waive a claim, and does not "
     "record the parties' legal position on a disputed matter."),
    ("8.3", "Subcontracting", "agreement",
     "{supplier} may subcontract performance only with {customer}'s prior written consent, which "
     "{customer} will not unreasonably withhold. {supplier} remains fully responsible for the acts "
     "and omissions of any subcontractor as if they were its own. A list of approved subcontractors "
     "is maintained in the Order."),
    ("11.4", "Suspension of Service", "agreement",
     "{supplier} may suspend performance on {suspend} days written notice if continuing would breach "
     "a law or put people or property at risk. {supplier} must narrow the suspension to the affected "
     "part and must restore performance as soon as the cause ends. This section is not a route to "
     "exit the Agreement and does not replace the termination provisions."),
    ("11.6", "Effect of Termination", "agreement",
     "On termination {customer} pays for items delivered and accepted before the termination date, "
     "and {supplier} returns or destroys {customer} Confidential Information on request. Termination "
     "does not affect a right or liability that accrued before it took effect. Sections that by "
     "their nature should survive do survive."),
    ("11.7", "Transition Assistance", "agreement",
     "On request made within thirty (30) days of a termination notice, {supplier} provides "
     "reasonable assistance to move the work to {customer} or to a replacement supplier, for up to "
     "ninety (90) days, at the rates in the Order. Transition assistance is a service, not a remedy, "
     "and requesting it does not extend the termination date."),
    ("12.1", "Indemnity", "agreement",
     "{supplier} will defend {customer} against a third party claim that an item supplied under this "
     "Agreement infringes a patent, copyright, or trade secret, and will pay damages finally awarded. "
     "{customer} must notify {supplier} promptly, give {supplier} control of the defense, and provide "
     "reasonable assistance at {supplier}'s cost."),
    ("12.5", "Insurance", "agreement",
     "{supplier} maintains commercial general liability cover of at least five million dollars "
     "($5,000,000) per occurrence and professional liability cover of at least two million dollars "
     "($2,000,000), and names {customer} as an additional insured. Carrying insurance does not cap "
     "or extend {supplier}'s liability, which is governed by the limitation of liability section."),
    ("13.4", "Force Majeure", "agreement",
     "Neither party is liable for a failure to perform caused by an event beyond its reasonable "
     "control, including natural disaster, war, and government action, provided it notifies the "
     "other promptly and works to resume performance. Inability to pay is never a force majeure "
     "event. If the event continues for more than sixty (60) days either party may terminate."),
    ("14.2", "Escalation and Dispute Resolution", "agreement",
     "Before starting proceedings, a party must escalate a dispute in writing to the other party's "
     "contract manager, who has fifteen (15) days to respond, and then to the executive sponsors, "
     "who have a further fifteen (15) days. This process is about resolving disagreements. It does "
     "not alter, pause, or extend any cure period or notice period elsewhere in this Agreement."),
    ("15.1", "Publicity", "agreement",
     "Neither party may use the other party's name, logo, or trade marks in a press release, case "
     "study, or customer list without prior written consent. Consent for one use is not consent for "
     "another. Either party may name the other in a confidential list of references given to a "
     "regulator or a prospective acquirer."),
    ("16.6", "Entire Agreement and Amendments", "agreement",
     "This Agreement and its Schedules, Exhibits, and Orders are the entire agreement between the "
     "parties on this subject and replace all earlier discussions. An amendment is effective only if "
     "it is in writing, identifies the section it changes, states its effective date, and is signed "
     "by an authorized representative of each party."),
    ("16.9", "No Waiver", "agreement",
     "A failure or delay in exercising a right under this Agreement is not a waiver of that right. A "
     "single or partial exercise does not prevent a further exercise. A waiver is effective only if "
     "it is in writing and signed by the party giving it, and applies only to the instance and the "
     "purpose for which it was given."),
]

EXTRA_NUMBERS = {
    "harbor": {"accept": "fifteen (15)", "suspend": "ten (10)"},
    "cedar": {"accept": "ten (10)", "suspend": "seven (7)"},
    "atlas": {"accept": "twenty (20)", "suspend": "fourteen (14)"},
}

for key, m in MATTERS.items():
    numbers = EXTRA_NUMBERS[key]
    for section, heading, kind, template in REST:
        add(
            key,
            f"s{section.replace('.', '-')}",
            document=m["agreement"],
            document_title=m["agreement_title"],
            section=section,
            heading=heading,
            instrument=kind,
            text=template.format(
                customer=m["customer"], supplier=m["supplier"], **numbers
            ),
        )

# Harbor's Section 11.1 is the one replaced by amendment. Close its window.
for p in PASSAGES:
    if p["passage_id"] == "harbor-cure":
        p["effective_to"] = "2026-04-01"
        p["status"] = "superseded"

# ---------------------------------------------------------------------------
# HARBOR
# A. Historical applicability: cure period, original versus Amendment No. 3.
# B. Evidence dependency: liability cap plus the Excluded Claims definition.
# C. Authority versus repetition: retention schedule versus a memo family.
# ---------------------------------------------------------------------------

add(
    "harbor",
    "am3-2",
    document="AMENDMENT-03",
    document_title="Amendment No. 3 to the Master Services Agreement",
    section="2",
    heading="Amendment of Section 11.1 (Cure Period)",
    instrument="amendment",
    executed="2026-02-18",
    effective_from="2026-04-01",
    references=["cure"],
    text=(
        "Section 2. Amendment of Section 11.1. From and after the Amendment Effective Date of April 1, 2026, "
        "Section 11.1 is deleted and replaced with the following: a party in material breach must cure that "
        "breach within fifteen (15) days after receipt of a written notice of default. A notice of default "
        "received before the Amendment Effective Date remains governed by Section 11.1 as originally executed, "
        "and the sixty (60) day cure period continues to run on that notice."
    ),
)
add(
    "harbor",
    "msa-13-1",
    document="MSA-2025",
    document_title="Master Services Agreement",
    section="13.1",
    heading="Limitation of Liability",
    references=["msa-1-14"],
    text=(
        "Except for Excluded Claims as defined in Section 1.14, each party's total aggregate liability arising "
        "out of or relating to this Agreement is limited to the fees paid or payable by Customer in the twelve "
        "(12) months preceding the event giving rise to the claim. This limit applies in the aggregate across "
        "all claims and all theories of liability. The scope of the exception is fixed by Section 1.14 and not "
        "by this Section."
    ),
)
add(
    "harbor",
    "msa-1-14",
    document="MSA-2025",
    document_title="Master Services Agreement",
    section="1.14",
    heading="Definition: Excluded Claims",
    references=["msa-13-1"],
    text=(
        "\"Excluded Claims\" means (a) a party's breach of Section 9 (Protected Health Information), (b) a "
        "party's indemnification obligations under Section 14, and (c) Customer's obligation to pay fees when "
        "due. Excluded Claims are not subject to the limitation of liability in Section 13.1, and liability for "
        "an Excluded Claim is limited only by applicable law."
    ),
)
add(
    "harbor",
    "msa-13-2",
    document="MSA-2025",
    document_title="Master Services Agreement",
    section="13.2",
    heading="Exclusion of Consequential Damages",
    text=(
        "Neither party is liable for indirect, incidental, special, punitive, or consequential damages, or for "
        "lost profits, lost revenue, or loss of goodwill, however caused and on any theory of liability. This "
        "exclusion applies even if the party was advised of the possibility of the damages and even if a remedy "
        "fails of its essential purpose. This Section addresses categories of damages and does not set a "
        "monetary cap."
    ),
)
add(
    "harbor",
    "exh-d1",
    document="EXHIBIT-D1",
    document_title="Exhibit D-1, Data Retention Schedule (superseded)",
    section="D-1",
    heading="Minimum Retention Periods by Record Class",
    instrument="exhibit",
    effective_to="2026-02-01",
    text=(
        "Minimum retention periods. Clinical records processed on behalf of Customer: three (3) "
        "years from the date of creation. System access logs: three (3) years. Billing and "
        "remittance records: three (3) years. This Exhibit is replaced by Exhibit D-2 with effect "
        "from 1 February 2026, and does not govern a record class after that date."
    ),
)
add(
    "harbor",
    "exh-d2",
    document="EXHIBIT-D2",
    document_title="Exhibit D-2, Data Retention Schedule",
    section="D-2",
    heading="Minimum Retention Periods by Record Class",
    instrument="exhibit",
    effective_from="2026-02-01",
    references=["exh-d1"],
    text=(
        "Minimum retention periods. Clinical records processed on behalf of Customer: seven (7) years from the "
        "date of creation. System access logs: three (3) years. Billing and remittance records: seven (7) "
        "years. Supplier must not delete a record class before the period stated in this Exhibit expires. A "
        "Customer instruction, a project plan, or an internal summary does not shorten a period fixed by this "
        "Exhibit."
    ),
)
for n, (label, when, author) in enumerate(
    [
        ("Executive digest", "2026-05-04", "the account director"),
        ("Delivery team update", "2026-05-06", "the delivery lead"),
        ("Storage planning note", "2026-05-11", "the platform team"),
        ("Weekly client briefing", "2026-05-18", "the client partner"),
        ("Archive clean-up brief", "2026-06-02", "the operations manager"),
    ],
    start=1,
):
    add(
        "harbor",
        f"retention-note-{n}",
        document=f"MEMO-RET-{100 + n}",
        document_title=f"Internal memorandum: Harbor retention window ({label})",
        section="1",
        heading=f"Harbor retention window, {label}",
        instrument="memo",
        executed=when,
        effective_from=when,
        family="retention-note",
        references=["exh-d2"],
        text=(
            f"Circulated by {author} for planning. Confirming for the delivery team that the retention window "
            f"under the Harbor engagement is three (3) years for all record classes, and that the archive "
            f"clean-up can be sized on a three-year horizon. This note summarizes the schedule for planning "
            f"purposes. It is not the schedule, and the schedule in Exhibit D-2 governs if the two differ."
        ),
    )

# ---------------------------------------------------------------------------
# CEDAR
# A. Historical applicability: uplift cap, original versus Amendment No. 1.
# B. Evidence dependency: service credits plus the Monthly Uptime definition.
# C. Authority versus repetition: renewal notice versus a deal desk memo family.
# ---------------------------------------------------------------------------

add(
    "cedar",
    "sub-6-2",
    document="SUB-2024",
    document_title="Subscription Agreement",
    section="6.2",
    heading="Annual Fee Adjustment",
    effective_to="2026-01-01",
    text=(
        "At each renewal, Supplier may increase the subscription fee for the following subscription year. The "
        "increase must not exceed the change in the Consumer Price Index over the preceding twelve (12) months "
        "plus three percentage points (CPI + 3%). Supplier must state the new fee in writing at least sixty "
        "(60) days before the renewal date. An increase stated later than that takes effect at the following "
        "renewal."
    ),
)
add(
    "cedar",
    "addendum-a",
    document="ADDENDUM-A",
    document_title="Addendum A, promotional pricing (expired)",
    section="A.1",
    heading="Promotional hold on the subscription fee",
    instrument="amendment",
    effective_to="2025-01-01",
    references=["sub-6-2"],
    text=(
        "For the promotional period ending 1 January 2025, Supplier will not increase the "
        "subscription fee at renewal, and the adjustment in Section 6.2 is held at zero percent "
        "(0%). This Addendum expires on its own terms on 1 January 2025. After expiry the "
        "adjustment in Section 6.2 applies to every later renewal without further notice."
    ),
)
add(
    "cedar",
    "am1-3",
    document="AMENDMENT-01",
    document_title="Amendment No. 1 to the Subscription Agreement",
    section="3",
    heading="Amendment of Section 6.2 (Annual Fee Adjustment)",
    instrument="amendment",
    executed="2025-12-05",
    effective_from="2026-01-01",
    references=["sub-6-2"],
    text=(
        "Section 3. Amendment of Section 6.2. From and after the Amendment Effective Date of January 1, 2026, "
        "the annual fee adjustment is capped at five percent (5%) of the then-current subscription fee, and the "
        "index-linked formula in Section 6.2 no longer applies. A renewal whose renewal date falls before the "
        "Amendment Effective Date remains governed by Section 6.2 as originally executed, including the CPI "
        "plus three percentage point cap. The sixty (60) day written notice requirement is unchanged."
    ),
)
add(
    "cedar",
    "sub-6-3",
    document="SUB-2024",
    document_title="Subscription Agreement",
    section="6.3",
    heading="Invoicing and Late Payment",
    text=(
        "Supplier invoices the subscription fee annually in advance. Undisputed invoices are payable within "
        "thirty (30) days of receipt. Amounts not paid when due accrue interest at one percent (1%) per month "
        "or the maximum rate permitted by law, whichever is lower. A good faith dispute over part of an invoice "
        "does not excuse payment of the undisputed remainder. This Section concerns payment mechanics and does "
        "not limit the size of a fee increase."
    ),
)
add(
    "cedar",
    "sla-4",
    document="SLA-2024",
    document_title="Service Level Agreement",
    section="4",
    heading="Service Credits",
    instrument="exhibit",
    references=["sla-1"],
    text=(
        "If Monthly Uptime, as defined in Section 1, falls below the Availability Target of 99.9% in any "
        "calendar month, Customer is entitled to a service credit against the following invoice: ten percent "
        "(10%) of the monthly fee for Monthly Uptime below 99.9%, and twenty-five percent (25%) for Monthly "
        "Uptime below 99.0%. Customer must request the credit within thirty (30) days after the end of the "
        "affected month. Whether a period of unavailability counts at all is determined by the definition in "
        "Section 1."
    ),
)
add(
    "cedar",
    "sla-1",
    document="SLA-2024",
    document_title="Service Level Agreement",
    section="1",
    heading="Definition: Monthly Uptime",
    instrument="exhibit",
    references=["sla-4"],
    text=(
        "\"Monthly Uptime\" means the percentage of minutes in a calendar month during which the Service "
        "responds to a valid request, excluding (a) Scheduled Maintenance Windows announced at least five (5) "
        "business days in advance, (b) unavailability caused by Customer configuration, Customer code, or "
        "Customer network, and (c) unavailability caused by a force majeure event. Minutes excluded under this "
        "definition are removed from the denominator and do not count as downtime for Section 4."
    ),
)
add(
    "cedar",
    "sub-9-1",
    document="SUB-2024",
    document_title="Subscription Agreement",
    section="9.1",
    heading="Support Response Times",
    text=(
        "Supplier responds to a Severity 1 ticket within one (1) hour, a Severity 2 ticket within four (4) "
        "business hours, and all other tickets within two (2) business days. A response is an acknowledgment "
        "with an assigned engineer, not a resolution. Missing a response time entitles Customer to escalation "
        "to the duty manager. This Section creates no monetary remedy and does not affect service credits."
    ),
)
add(
    "cedar",
    "sub-3-1",
    document="SUB-2024",
    document_title="Subscription Agreement",
    section="3.1",
    heading="Term and Renewal",
    text=(
        "The initial subscription term is twelve (12) months from the Effective Date. The subscription renews "
        "automatically for successive twelve (12) month terms unless a party gives written notice of "
        "non-renewal at least ninety (90) days before the end of the then-current term. Notice given later than "
        "ninety (90) days before the renewal date takes effect at the following renewal. Notice of "
        "non-renewal stops the next term; it is different from termination under Section 11.2."
    ),
)
for n, (label, when, author) in enumerate(
    [
        ("Deal desk summary", "2026-04-09", "the deal desk"),
        ("Customer success update", "2026-04-15", "the customer success manager"),
        ("Renewal forecast note", "2026-04-21", "the regional sales lead"),
        ("Quarterly account briefing", "2026-05-07", "the account executive"),
    ],
    start=1,
):
    add(
        "cedar",
        f"renewal-note-{n}",
        document=f"MEMO-REN-{200 + n}",
        document_title=f"Internal memorandum: Cedar renewal terms ({label})",
        section="1",
        heading=f"Cedar renewal terms, {label}",
        instrument="memo",
        executed=when,
        effective_from=when,
        family="renewal-note",
        references=["sub-3-1"],
        text=(
            f"Prepared by {author} for the pipeline review. Cedar is on a rolling subscription and can cancel "
            f"at any time on thirty (30) days written notice, so the renewal should be forecast as low risk. "
            f"Teams should not commit to a non-renewal deadline with the customer on the basis of this note. "
            f"The term and renewal provision in the Subscription Agreement controls."
        ),
    )

# ---------------------------------------------------------------------------
# ATLAS
# A. Historical applicability: rejection window, original versus Amendment No. 2.
# B. Evidence dependency: warranty plus the warranty exclusion.
# C. Authority versus repetition: change approval versus a memo family.
# ---------------------------------------------------------------------------

add(
    "atlas",
    "sup-4-2",
    document="SUP-2024",
    document_title="Supply Agreement",
    section="4.2",
    heading="Acceptance and Rejection of Goods",
    effective_to="2026-06-01",
    text=(
        "Buyer may inspect Goods after delivery and may reject Goods that do not conform to the specification "
        "by giving written notice of rejection within thirty (30) days after delivery. Goods not rejected "
        "within that period are deemed accepted. A notice of rejection must identify the lot, the quantity "
        "rejected, and the nonconformity observed. Acceptance does not waive a warranty claim under Section 8."
    ),
)
add(
    "atlas",
    "am2-1",
    document="AMENDMENT-02",
    document_title="Amendment No. 2 to the Supply Agreement",
    section="1",
    heading="Amendment of Section 4.2 (Rejection Window)",
    instrument="amendment",
    executed="2026-05-11",
    effective_from="2026-06-01",
    references=["sup-4-2"],
    text=(
        "Section 1. Amendment of Section 4.2. From and after the Amendment Effective Date of June 1, 2026, the "
        "period for giving written notice of rejection is ten (10) business days after delivery, and Goods not "
        "rejected within that period are deemed accepted. Goods delivered before the Amendment Effective Date "
        "remain governed by Section 4.2 as originally executed, and the thirty (30) day rejection window "
        "continues to apply to those deliveries. Section 8 is unchanged."
    ),
)
add(
    "atlas",
    "sup-4-3",
    document="SUP-2024",
    document_title="Supply Agreement",
    section="4.3",
    heading="Inspection at Delivery",
    text=(
        "Buyer's receiving staff must count cartons and record visible transit damage on the carrier's delivery "
        "record at the time of delivery. Damage recorded in this way is handled as a carrier claim. Signing the "
        "delivery record confirms the count and the external condition of the shipment only. This Section does "
        "not start, shorten, or replace the period for giving notice of rejection."
    ),
)
add(
    "atlas",
    "sup-8-1",
    document="SUP-2024",
    document_title="Supply Agreement",
    section="8.1",
    heading="Warranty",
    references=["sup-8-4"],
    text=(
        "Supplier warrants that Goods conform to the specification and are free from defects in material and "
        "workmanship. If a Good fails to meet this warranty, Supplier must, at Buyer's election, repair it, "
        "replace it, or refund the purchase price. This warranty is subject to the exclusions in Section 8.4, "
        "and the remedies in this Section are Buyer's exclusive warranty remedies."
    ),
)
add(
    "atlas",
    "sup-8-4",
    document="SUP-2024",
    document_title="Supply Agreement",
    section="8.4",
    heading="Warranty Exclusions",
    references=["sup-8-1"],
    text=(
        "The warranty in Section 8.1 does not apply to a Good that has been modified, reworked, or repaired by "
        "Buyer or by a third party without Supplier's prior written approval, to a Good used outside the "
        "operating limits in the specification, or to normal wear of a consumable part. A Good excluded by this "
        "Section carries no warranty remedy, regardless of when the defect appears within the warranty period."
    ),
)
add(
    "atlas",
    "sup-8-2",
    document="SUP-2024",
    document_title="Supply Agreement",
    section="8.2",
    heading="Warranty Period",
    text=(
        "The warranty in Section 8.1 runs for eighteen (18) months from the date of delivery or twelve (12) "
        "months from the date of first use, whichever ends first. A repaired or replaced Good carries the "
        "remainder of the original period or ninety (90) days, whichever is longer. This Section fixes the "
        "duration of the warranty and does not decide whether a particular Good is covered."
    ),
)
add(
    "atlas",
    "sup-5-3",
    document="SUP-2024",
    document_title="Supply Agreement",
    section="5.3",
    heading="Engineering Changes and Substitutions",
    text=(
        "Supplier must not substitute a component, change a process, or change a source of supply without "
        "Buyer's prior written approval issued through an Engineering Change Notice. An approval that is stated "
        "to be conditional takes effect only when the stated condition is satisfied and Buyer confirms that in "
        "writing. Goods built on an unapproved change are nonconforming, whatever their measured performance."
    ),
)
add(
    "atlas",
    "ecn-109",
    document="ECN-109",
    document_title="Engineering Change Notice 109, harness routing (withdrawn)",
    section="109",
    heading="Withdrawn approval of connector 8841-B",
    instrument="operational_record",
    executed="2026-01-15",
    effective_from="2026-01-15",
    effective_to="2026-02-20",
    references=["sup-5-3"],
    text=(
        "Engineering Change Notice 109. Buyer approved substitution of the servo connector from "
        "part 8841-A to part 8841-B without condition. Buyer withdrew this notice on 20 February "
        "2026 after the harness routing failed qualification. Nothing in this notice approves any "
        "other part number, and a later change to a different part requires its own notice."
    ),
)
add(
    "atlas",
    "ecn-114",
    document="ECN-114",
    document_title="Engineering Change Notice 114, servo connector substitution",
    section="114",
    heading="Conditional approval of connector substitution",
    instrument="operational_record",
    executed="2026-03-09",
    effective_from="2026-03-09",
    references=["sup-5-3"],
    text=(
        "Engineering Change Notice 114. Buyer conditionally approves substitution of the servo connector from "
        "part 8841-A to part 8841-C, conditioned on a passing first article inspection of thirty (30) units "
        "and written confirmation from Buyer's quality engineer. As of this notice the first article inspection "
        "has not been completed and no confirmation has issued. Production against this change is not approved "
        "until both conditions are satisfied."
    ),
)
# Not every memo is noise. This one is the only record of whether the first
# article inspection passed, so a team that down-weights memos as a class
# loses the answer to that question. Authority is about what a document
# records, not about what kind of document it is.
add(
    "atlas",
    "qa-memo",
    document="MEMO-QA-410",
    document_title="Quality memorandum: first article inspection, connector 8841-C",
    section="1",
    heading="First article inspection result, 8841-C",
    instrument="memo",
    executed="2026-04-20",
    effective_from="2026-04-20",
    family="qa-inspection",
    references=["ecn-114"],
    text=(
        "First article inspection of the 8841-C servo connector was carried out on 18 April 2026 "
        "on a sample of thirty units. Two units failed the dimensional check at the retention "
        "shoulder and one failed the pull test. The inspection is therefore recorded as not "
        "passed. No further sample has been submitted, and quality has issued no confirmation "
        "under Engineering Change Notice 114."
    ),
)

for n, (label, when, author) in enumerate(
    [
        ("Program status digest", "2026-03-12", "the program manager"),
        ("Supplier quality update", "2026-03-17", "the supplier quality engineer"),
        ("Line readiness note", "2026-03-24", "the manufacturing lead"),
        ("Weekly build briefing", "2026-04-02", "the production planner"),
        ("Cost savings summary", "2026-04-13", "the commodity manager"),
    ],
    start=1,
):
    add(
        "atlas",
        f"change-note-{n}",
        document=f"MEMO-ECN-{300 + n}",
        document_title=f"Internal memorandum: connector substitution status ({label})",
        section="1",
        heading=f"Connector substitution status, {label}",
        instrument="memo",
        executed=when,
        effective_from=when,
        family="change-note",
        references=["ecn-114"],
        text=(
            f"Circulated by {author}. The connector substitution from 8841-A to 8841-C is approved and the "
            f"line can build to the new configuration, so the cost saving can be booked this quarter. This "
            f"note reports the program view for scheduling. The Engineering Change Notice and Section 5.3 of "
            f"the Supply Agreement state the approval status that governs."
        ),
    )


BY_ID = {p["passage_id"]: p for p in PASSAGES}
