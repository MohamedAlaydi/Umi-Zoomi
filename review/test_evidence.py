import unittest

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from assay_transfer import WT, SCORES, auc_positive_first, comparison, spr_population
from evaluate_pairs import evaluate
from panel import hamming, prioritize
from structure_checks import footprint, pair_scores


class EvidenceTests(unittest.TestCase):
    def test_no_fit_is_a_separate_outcome_and_replicates_do_not_add_votes(self):
        def row(loop, outcome, kd):
            return dict(cdrh3=loop,vh_sequence="A"*98+loop+"Y",vl_sequence="VL",
                        kd_nM=kd,binding_result=outcome)
        a,b,c,d = ["A"*9 + terminal for terminal in "GSVY"]
        items = [row(WT,"quantified_binding",.15),row(WT,"quantified_binding",.03),
                 row(a,"quantified_binding",1.),row(a,"quantified_binding",3.),
                 row(b,"no_reportable_kd",np.nan),row(c,"inconclusive",np.nan),
                 row(d,"quantified_binding",2.)]
        sample,meta = spr_population(pd.DataFrame(items),{d})
        self.assertEqual(meta["wt_n"],2)
        self.assertEqual(dict(zip(sample.cdrh3,sample.outcome)),{a:"quantified_binding",b:"no_reportable_kd",c:"inconclusive"})
        self.assertEqual(sample.set_index("cdrh3").at[a,"kd"],2.)
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            spr_population(pd.DataFrame(items+[row(a,"no_reportable_kd",np.nan)]),{d})

    def test_paired_auc_scores_ties_like_sklearn(self):
        x=np.array([[2,3],[1,0],[1,3],[0,1],[1,3]])
        expected=[roc_auc_score([1,1,0,0,0],column) for column in x.T]
        np.testing.assert_allclose(auc_positive_first(x,2),expected)

    def test_extra_comparator_participates_in_each_paired_endpoint(self):
        frame = pd.DataFrame({"outcome":["quantified_binding"]*12+["no_reportable_kd"]*12,
                              "kd":list(range(1,13))+[np.nan]*12,"distance":[4]*24})
        names = SCORES+["extra"]
        for name in names:
            frame[name] = np.arange(24)
        result = comparison(frame,10,np.random.default_rng(1),names)
        for field in ("auc","rho_log_kd","same_distance_auc"):
            self.assertEqual(set(result[field]),set(names))
        self.assertEqual(result["delta_auc_blosum_minus"]["extra"]["value"],0.)

    def test_chain_order_asymmetry_and_internal_interface_exclusion(self):
        order=["D","B","C","A"]
        m=np.eye(4);m[0,1]=.4;m[1,0]=.6;m[1,2]=.8;m[2,1]=.7
        m[1,3]=1;m[3,1]=1
        result=pair_scores(m,order)
        self.assertAlmostEqual(result["VH_min"],.5)
        self.assertAlmostEqual(result["BC"],.75)
        self.assertAlmostEqual(result["Fv_mean"],1.25/4)
        with self.assertRaises(ValueError):
            pair_scores(m,["D","B","C","C"])

    def test_light_chain_contact_counts_and_author_fragment_ids_survive(self):
        atoms=(np.array(["A","B","C","D"]), np.array([28,99,580,591]),
               np.array([[0.,0.,0.],[20.,0.,0.],[4.4,0.,0.],[24.6,0.,0.]]))
        self.assertEqual(footprint(atoms,4.5),({("C",580)},set()))
        self.assertEqual(footprint(atoms,5.),({("C",580),("D",591)},{99}))

    def test_panel_is_order_invariant_and_only_uses_distinct_qualified_loops(self):
        def candidate(name, loop, source, seq, confidence, margin=True):
            return dict(query=name, cdrh3=loop, source=source, blosum62=seq, local_margin=margin,
                        local_distance=3, metrics={"VH_min":confidence},
                        footprint={"4.5":{"jaccard":.9}})
        batch = [candidate("trastuzumab_wt",WT,"control",100,.9,False),
                 candidate("unsupported","K"*10,"enumerated",100,.98,False),
                 candidate("sequence","A"*10,"enumerated",30,.91),
                 candidate("duplicate","A"*9+"S","enumerated",29,.92),
                 candidate("discordant","V"*10,"enumerated",40,.88),
                 candidate("geometry","T"*10,"enumerated",20,.95),
                 candidate("r004_free","S"*10,"control",10,.96)]
        result = prioritize(batch)
        self.assertEqual([r["query"] for r in result],["sequence","discordant","geometry","r004_free"])
        self.assertEqual(result,prioritize(list(reversed(batch))))
        self.assertTrue(all(hamming(x["cdrh3"],y["cdrh3"]) >= 3
                            for i,x in enumerate(result) for y in result[i+1:]))

    def test_new_pair_abstains_on_unmatched_framework_and_identifies_wt(self):
        ref = dict(vh_sequence="A"*98+WT+"Y",vl_sequence="VL")
        pair = dict(query="probe",heavy_variable=ref["vh_sequence"],light_variable="VL")
        pool = {10:np.frombuffer(WT.encode(),dtype=np.uint8).reshape(1,10)}
        self.assertEqual(evaluate(pair,ref,pool)["assessment"],"reference")
        query = {**pair,"heavy_variable":"A"*98+"A"*10+"Y"}
        result = evaluate(query,ref,pool)
        self.assertEqual(result["assessment"],"scored")
        self.assertTrue(result["local_margin"])
        result = evaluate({**query,"light_variable":"VV"},ref,pool)
        self.assertEqual(result["assessment"],"outside_reviewed_background")
        self.assertEqual(result["blosum62"],"")


if __name__ == "__main__":
    unittest.main()
