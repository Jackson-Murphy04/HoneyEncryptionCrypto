"""Evaluate the non-uniform weighted DTE against its declared synthetic prior."""
from __future__ import annotations
import argparse, json, secrets, time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from scipy.stats import chisquare
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import honey, weighted_dte


def run(trials: int, out: Path) -> dict:
    if trials < honey.MESSAGE_COUNT: raise ValueError("trials must be >= message count")
    started=time.perf_counter(); counts=Counter()
    for _ in range(trials):
        m=weighted_dte.decode(secrets.token_bytes(honey.SEED_BYTES))
        counts[honey.MESSAGES.index(m)] += 1
    runtime=time.perf_counter()-started
    probs=weighted_dte.target_probabilities()
    observed=[counts.get(i,0) for i in range(honey.MESSAGE_COUNT)]
    expected=[trials*p for p in probs]
    chi,p=chisquare(observed,f_exp=expected)
    empirical=[n/trials for n in observed]
    tv=0.5*sum(abs(a-b) for a,b in zip(empirical,probs))
    result={"experiment":"weighted non-uniform DTE seed-decoding evaluation",
      "generated_utc":datetime.now(timezone.utc).isoformat(),"trials":trials,
      "message_count":honey.MESSAGE_COUNT,"synthetic_prior":"product of declared location, weekday, and time weights in weighted_dte.py",
      "chi_square_statistic":float(chi),"degrees_of_freedom":honey.MESSAGE_COUNT-1,
      "chi_square_p_value":float(p),"total_variation_distance":tv,
      "min_expected_count":min(expected),"max_expected_count":max(expected),
      "min_observed_count":min(observed),"max_observed_count":max(observed),
      "runtime_seconds":runtime,"target_probabilities":probs,"observed_counts":observed,
      "caveat":"This checks sampling from a hand-authored synthetic prior, not the distribution of actual meeting messages or cryptographic indistinguishability."}
    out.mkdir(parents=True,exist_ok=True)
    (out/'weighted_dte_results.json').write_text(json.dumps(result,indent=2)+'\n')
    with (out/'weighted_dte_frequencies.csv').open('w') as f:
      f.write('message,weight,target_probability,observed_count,observed_probability\n')
      for i,m in enumerate(honey.MESSAGES):
        f.write(f'"{m}",{weighted_dte.WEIGHTS[i]},{probs[i]:.12g},{observed[i]},{empirical[i]:.12g}\n')
    indices=list(range(honey.MESSAGE_COUNT))
    plt.figure(figsize=(13,4.5))
    plt.plot(indices, probs, label='Target probability', linewidth=1.8)
    plt.plot(indices, empirical, label='Observed probability', linewidth=1.0, alpha=0.8)
    plt.xlabel('Message index (see weighted_dte_frequencies.csv)')
    plt.ylabel('Probability')
    plt.title('Weighted DTE: target and observed message probabilities')
    plt.legend()
    plt.tight_layout()
    plt.savefig(out/'weighted_dte_distribution.png',dpi=160)
    plt.close()
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--trials',type=int,default=560000);p.add_argument('--output',type=Path,default=Path(__file__).resolve().parent/'evaluation_results');a=p.parse_args()
    print(json.dumps(run(a.trials,a.output),indent=2))
