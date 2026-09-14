"""Panel content for the web app.

Encoded on purpose, and this is the reason why. The applicability rules are the
legal half of the exercise. They render in the browser so a person reads them
and decides what to do. They are encoded so that a coding agent pointed at this
repository does not absorb the legal judgment by grepping for it and hand back
an answer the person never reasoned about.

This raises the bar. It is not a security boundary, and nothing here pretends
to be one: anyone who decodes this has decided to, which is a different act
from stumbling across it. The real separation in this workshop is that the
held-out questions are not in the participant repository at all.

AGENTS.md deliberately does give an agent the mechanical facts, the payload
fields and the existence of extra vectors, so nobody burns thirty minutes
rediscovering the repository. The mechanics are not the lesson. The judgment is.
"""

import base64
import json

_PANEL = (
    "W1siQSBxdWVzdGlvbiBoYXMgYSBkYXRlLCBhbmQgZXZpZGVuY2UgaGFzIGEgbGlmZSIsICJFdmVyeSBxdWVzdGlvbiBp"
    "cyBhc2tlZCBvbiBhIGRhdGUuIEEgZG9jdW1lbnQgaXMgZXZpZGVuY2UgZm9yIHRoYXQgcXVlc3Rpb24gb25seSBpZiBp"
    "dCB3YXMgaW4gZm9yY2Ugb24gdGhhdCBkYXRlLiBOb3QgaW4gZm9yY2UgdG9kYXkuIEluIGZvcmNlIHRoZW4uIl0sIFsi"
    "QSByZXBsYWNlZCBjbGF1c2Ugc3RpbGwgZ292ZXJucyBpdHMgb3duIHBlcmlvZCIsICJBIGNsYXVzZSB0aGF0IGhhcyBz"
    "aW5jZSBiZWVuIHJlcGxhY2VkIGlzIHRoZSBjb3JyZWN0IGFuc3dlciB0byBhIHF1ZXN0aW9uIGRhdGVkIHdoaWxlIGl0"
    "IGdvdmVybmVkLiBGaWx0ZXJpbmcgb3V0IGV2ZXJ5dGhpbmcgbWFya2VkIHN1cGVyc2VkZWQgdGhyb3dzIGF3YXkgdGhl"
    "IHJpZ2h0IGFuc3dlciB0byBleGFjdGx5IHRoZSBxdWVzdGlvbnMgdGhhdCB0dXJuIG9uIGhpc3RvcnkuIl0sIFsiQSB3"
    "aW5kb3cgdGhhdCBlbmRzIG9uIHRoZSBxdWVzdGlvbiBkYXRlIGhhcyBhbHJlYWR5IGNsb3NlZCIsICJJZiBhbiBhbWVu"
    "ZG1lbnQgdGFrZXMgZWZmZWN0IG9uIDEgQXByaWwsIHRoZW4gb24gMSBBcHJpbCB0aGUgb2xkIGNsYXVzZSBubyBsb25n"
    "ZXIgZ292ZXJucy4gVGhlIGVuZCBvZiBhbiBlZmZlY3RpdmUgcGVyaW9kIGlzIGV4Y2x1c2l2ZS4gT25lIGRheSBlaXRo"
    "ZXIgd2F5IGNoYW5nZXMgdGhlIGFuc3dlciwgYW5kIHRoZSBxdWVzdGlvbnMgZGF0ZWQgb24gYSBjaGFuZ2VvdmVyIGV4"
    "aXN0IHRvIGNhdGNoIHRoYXQuIl0sIFsiRXZpZGVuY2UgY29tZXMgZnJvbSB0aGlzIGNsaWVudCdzIGZpbGUiLCAiVGhl"
    "IHN0b3JlIGhvbGRzIG90aGVyIGNsaWVudHMnIGNvbnRyYWN0cy4gQSBjbGF1c2UgdGhhdCByZWFkcyBwZXJmZWN0bHkg"
    "YW5kIGJlbG9uZ3MgdG8gYW5vdGhlciBtYXR0ZXIgaXMgYSBjb25maWRlbnRpYWxpdHkgaW5jaWRlbnQsIGFuZCBpdCBp"
    "cyB0aGUgc2luZ2xlIG1vc3QgZXhwZW5zaXZlIGZhaWx1cmUgaW4gdGhpcyBleGVyY2lzZS4iXSwgWyJUaGUgaW5zdHJ1"
    "bWVudCBnb3Zlcm5zLCB0aGUgbWVtbyByZXBvcnRzIiwgIkludGVybmFsIHN1bW1hcmllcywgYWNjb3VudCBub3Rlcywg"
    "YW5kIGJyaWVmaW5nIGRpZ2VzdHMgZGVzY3JpYmUgd2hhdCBzb21lb25lIGJlbGlldmVkLiBUaGUgc2NoZWR1bGUsIHRo"
    "ZSBhbWVuZG1lbnQsIGFuZCB0aGUgZXhlY3V0ZWQgZXhoaWJpdCBzYXkgd2hhdCBpcyBhZ3JlZWQuIFdoZW4gdGhleSBk"
    "aXNhZ3JlZSwgdGhlIGluc3RydW1lbnQgZ292ZXJucyBhbmQgdGhlIG1lbW8gaXMgZXZpZGVuY2Ugb25seSBvZiB3aGF0"
    "IHdhcyBjaXJjdWxhdGVkLiJdLCBbIkZpdmUgY29waWVzIG9mIG9uZSBub3RlIGlzIG9uZSBzb3VyY2UiLCAiRml2ZSBj"
    "b3BpZXMgb2YgdGhlIHNhbWUgbm90ZSwgZm9yd2FyZGVkIGJ5IGZpdmUgcGVvcGxlLCBpcyBvbmUgc291cmNlLiBDb3Vu"
    "dGluZyBpdCBmaXZlIHRpbWVzIGlzIGhvdyBhIGNvbmZpZGVudCB3cm9uZyBhbnN3ZXIgZ2V0cyBidWlsdC4gRGVkdXBs"
    "aWNhdGluZyBieSBkb2N1bWVudCBpZGVudGlmaWVyIGRvZXMgbm90IGhlbHAsIGJlY2F1c2UgZWFjaCBjb3B5IGhhcyBp"
    "dHMgb3duIGlkZW50aWZpZXIuIl0sIFsiQSBjbGF1c2UgYW5kIGl0cyBleGNlcHRpb24gYXJlIG9uZSBhbnN3ZXIiLCAi"
    "QW4gb3BlcmF0aXZlIGNsYXVzZSB0aGF0IGlzIGV4cHJlc3NseSBzdWJqZWN0IHRvIGEgZGVmaW5pdGlvbiBvciBhbiBl"
    "eGNsdXNpb24gaXMgb25seSBoYWxmIHRoZSBhbnN3ZXIuIFJldHJpZXZpbmcgdGhlIGNsYXVzZSBhbG9uZSBwcm9kdWNl"
    "cyBhIGNvbmZpZGVudCBhbnN3ZXIgaW4gdGhlIHdyb25nIGRpcmVjdGlvbi4gVGhlIGJ1bmRsZSBpcyB0aGUgZXZpZGVu"
    "Y2UuIl0sIFsiQSBtZW1vIGNhbiBiZSB0aGUgb25seSByZWNvcmQgb2YgYSBmYWN0IiwgIlRoZSBydWxlcyBhYm92ZSBh"
    "cmUgYWJvdXQgYXV0aG9yaXR5IG92ZXIgd2hhdCBhbiBhZ3JlZW1lbnQgbWVhbnMuIFdoZXRoZXIgYW4gaW5zcGVjdGlv"
    "biBoYXBwZW5lZCwgYW5kIHdoYXQgaXQgZm91bmQsIGlzIGEgcXVlc3Rpb24gb2YgZmFjdCwgYW5kIHNvbWV0aW1lcyB0"
    "aGUgb25seSBjb250ZW1wb3JhbmVvdXMgcmVjb3JkIG9mIGl0IGlzIGFuIGludGVybmFsIG1lbW8uIFJhbmsgb24gd2hh"
    "dCBhIGRvY3VtZW50IHJlY29yZHMsIG5vdCBvbiB3aGF0IGtpbmQgb2YgZG9jdW1lbnQgaXQgaXMuIl1d"
)

RULES = [tuple(rule) for rule in json.loads(base64.b64decode(_PANEL))]
