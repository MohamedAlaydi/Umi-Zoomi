# Decision log

Judgment is 40 % of the score and they want to know *why*, so write the
reason here the moment you make a call. One line each, newest at the bottom.

| time | who | decision | why |
| --- | --- | --- | --- |
| 09:40 | mohamed | Rank on min_ipae, iptm, binder_plddt | The `pass` column comes out empty for the HER2 exercise, which the Apheris docs say to expect |
| 09:45 | mohamed | Internal bar: CDRH3 min distance >= 3 and identity to trastuzumab <= 60 % | The published limits are distance >= 2 and <= 70 %. The task PDF says "under 70 %", the slides say "at most 70 %". A design on the line may be rejected, and a rejected design is worth nothing, so we keep a margin |
| 09:45 | mohamed | Built our own novelty check instead of waiting for abguard | abguard is not installed on the VM although the task PDF says it is. Ours implements the two published numeric rules over all 525,063 provided CDRH3s |
