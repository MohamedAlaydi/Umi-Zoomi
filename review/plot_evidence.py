"""Render the pitch figure from completed audit outputs. Write to a new PNG."""
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt


def main():
    folder, destination = map(Path,sys.argv[1:3])
    assay = json.loads((folder/"assay_transfer.json").read_text())
    structure = json.loads((folder/"structure_checks.json").read_text())
    candidates = [r for r in structure["batch"] if r["source"] != "control"]
    four_contact = sum({99,103,104,105} <= set(r["footprint"]["4.5"]["contacting_loop_positions"])
                       for r in candidates)
    fig,(left,right) = plt.subplots(1,2,figsize=(11.5,4.5),gridspec_kw={"width_ratios":[1.3,1]})
    fig.subplots_adjust(left=.09,right=.98,top=.76,bottom=.22,wspace=.40)
    palette = ["#146D67","#AE5828","#364963"]
    for idx,(key,label) in enumerate([("blosum62","BLOSUM62"),("identity","Parent identity"),("facs","FACS model")]):
        for group,field in enumerate(["all_variants","distance_4_to_6"]):
            est=assay[field]["auc"][key]
            center=est["value"];lo,hi=est["ci95"];x=group+(idx-1)*.17
            left.errorbar(x,center,yerr=[[center-lo],[hi-center]],fmt="o",color=palette[idx],
                          markersize=7,capsize=4,lw=1.7,label=label if group==0 else None)
    left.axhline(.5,color="#999999",linestyle=":",lw=1)
    left.set(xlim=(-.4,1.4),ylim=(.49,.94),ylabel="AUROC for reporting an SPR fit",
             xticks=[0,1],xticklabels=["All variants\n152 fits / 432 no fit","4–6 mutations\n82 fits / 128 no fit"])
    left.set_title("Can the sequence score transfer to SPR?",loc="left",fontsize=13)
    left.legend(frameon=False,fontsize=8,ncol=3,loc="upper center",handletextpad=.25,columnspacing=.7)
    right.barh([1,0],[len(candidates),four_contact],color=["#8293A7","#146D67"],height=.5)
    right.set(yticks=[1,0],yticklabels=["Four reference\nresidues retained","All four contact HER2\nin predicted pose"],
              xlim=(0,44),xticks=[0,10,20,30,40],xlabel="Candidates in run 006")
    right.set_title("What did anchoring preserve?",loc="left",fontsize=13)
    for y,n in [(1,len(candidates)),(0,four_contact)]:
        right.text(n+.45,y,str(n),va="center",fontsize=10)
    for ax in (left,right):
        ax.spines[["top","right"]].set_visible(False)
        ax.tick_params(labelsize=9)
    fig.suptitle("Trastuzumab selection under a limited assay budget",x=.09,y=.98,ha="left",fontsize=17)
    fig.text(.09,.035,"Left: unique FACS-unseen non-WT constructs; 95% paired-bootstrap intervals.   Right: 4.5 Å, one templated Boltz-2 sample.",fontsize=9)
    with destination.open("xb") as handle:
        fig.savefig(handle,format="png",dpi=185,bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
