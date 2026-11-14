# Decision log

Judgment is 40 % of the score and they want to know *why*, so write the
reason here the moment you make a call. One line each, newest at the bottom.

| time | who | decision | why |
| --- | --- | --- | --- |
| 09:40 | mohamed | Rank on min_ipae, iptm, binder_plddt | The `pass` column comes out empty for the HER2 exercise, which the Apheris docs say to expect |
| 09:45 | mohamed | Internal bar: CDRH3 min distance >= 3 and identity to trastuzumab <= 60 % | The published limits are distance >= 2 and <= 70 %. The task PDF says "under 70 %", the slides say "at most 70 %". A design on the line may be rejected, and a rejected design is worth nothing, so we keep a margin |
| 09:45 | mohamed | Built our own novelty check instead of waiting for abguard | abguard is not installed on the VM although the task PDF says it is. Ours implements the two published numeric rules over all 525,063 provided CDRH3s |
| 10:40 | mohamed | Mutate both D102 and M107, keep W99/G103/F104/Y105 | The contact map from 1N8Z shows only 4 of the 10 redesigned CDRH3 positions touch HER2. AMASS records confirm D102 isomerization (Harris 2001, Spanov 2022) and M107 oxidation (Hensel 2011, monitored in the CT-P6 biosimilar) as the two documented liabilities, and both sit at non-contact positions |
| 10:45 | mohamed | Corrected an earlier claim: Met-107 IS oxidation-prone | Web search said it was not. AMASS primary records say it is and that a biosimilar manufacturer measures it. Checking in AMASS rather than a review stopped us leaving a liability in the design |
| 11:05 | mohamed | Rank on contact conservation BEFORE the confidence scores | In the baseline, the design with the best numbers (her2_cdrh3_3, iptm 0.965, min_ipae 0.310) had lost 2 of its 4 HER2 contact residues. The design with worse numbers kept 3. So iptm does not track epitope preservation, and ranking on it alone would pick designs that may have moved off the epitope |
