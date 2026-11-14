# Umi Zoomi: slide-by-slide script

About 3 minutes of speech. Allow 4–5 minutes with animations and pauses. Read only the quoted text. Space/Right advances; Left goes back; F is fullscreen; M mutes. The live deck has 10 stops and 22 forward presses. The PDF has 13 pages.

## Slide 1: Title | PDF 1
Two presses: alarm, then title.

“We are Umi Zoomi. We chose four antibody variants to test against HER2. Here is why we chose them.”

## Slide 2: Motivation | PDF 2
Two presses reveal the two cards.

“Trastuzumab is an established treatment for HER2-positive breast cancer. We started from its antibody sequence and asked whether changes could improve binding or stability while keeping the same binding site.”

## Slide 3: Who needs this? | PDF 3
One press.

“Antibody discovery teams can generate many designs. The difficult decision is which ones to make and test. That is the problem our workflow addresses.”

## Slide 4: The binding site | PDF 4
One press.

“We used the known trastuzumab structure to locate the binding site, then checked new sequences against the whole HER2 protein.”

## Slide 5: Method | PDF 5
One press; allow the three labels to appear.

“We trained models on the organisers’ screening and affinity measurements, generated new sequences, and checked their predicted structures. We used Apheris, JapanFold and Nebius for the design and evaluation work. The code and validation records are in GitHub.”

## Slide 6: Findings | PDF 6
Three presses, one per card.

“The screening score and affinity predictions did not always agree, so we kept both. We also found that one docking model missed the known site for trastuzumab itself. We stopped using its negative results to reject candidates.

For stability, we chose two changes reported in the literature and applied them to selected designs.”

## Slide 7: Selection | PDF 7
Four presses through the funnel.

“We filtered the proposals for novelty and ranked the remaining designs. Our first four all pass local abguard. They cover three binding loops and two modified versions of the supporting structure.”

## Slide 8: The four picks | PDF 8–11
Four presses, one per candidate.

### Pick 01
“This is our leading binding-loop candidate from the affinity models.”

### Pick 02
“This has the same binding loop as Pick 01, with two changes to the supporting structure. Comparing the pair tests what those changes do.”

### Pick 03
“This uses a different loop and has the highest screening-model score among the four.”

### Pick 04
“This uses a third loop with the same two changes as Pick 02.”

## Slide 9: Results | PDF 12
Three presses reveal the cards. The figure stays visible.

“Mol 1 predicts that all four contact the nineteen HER2 residues in trastuzumab’s known binding site. That tells us where the model places them; it does not tell us how strongly they bind.

We have not measured binding or thermal stability. The next step is Adaptyv’s binding, competition and heat-stability tests, alongside trastuzumab.”

## Slide 10: Close | PDF 13
One press.

“If those tests are promising, the next stage is cell testing and checks for unwanted binding. Today we have four sequences ready for testing, a reason for each choice, and a documented workflow for the next round.”

## Preparation notes, not spoken

The talk covers judgment through the controls and four choices; execution through the implemented workflow and GitHub; user fit through antibody discovery teams; and path to value through laboratory and cell testing.

Pick 01 = newML_b973259db36d. Pick 02 = newML_b973259db36d_FW85N87T. Pick 03 = newML_a7acfcc8dce3. Pick 04 = newML_5753ea077281_FW85N87T.

The supporting-structure substitutions are S85N/R87T, using the paper’s verified numbering. The reported stability benefit was in full trastuzumab, not these new fragments. They also add a potential glycosylation site. Transfer to our designs remains to be tested.

The full model comparison is in MODEL_CONTROL.svg and MODEL_CONTROL_NOTES.md. Keep it available for questions.
