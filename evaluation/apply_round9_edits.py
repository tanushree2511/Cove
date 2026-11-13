"""Round-9 review fixes: sweep claims for all three methods, 'web family photos', orders, abstract/discussion rewrite, trims."""
p = r"D:\wincode\Major-Project\paper\v2\cove_paper.tex"
s = open(p, encoding="utf8").read()


def rep(a, b):
    global s
    assert a in s, a[:80]
    s = s.replace(a, b, 1)


def cut(start, end, new=""):
    global s
    i = s.index(start)
    j = s.index(end, i)
    s = s[:i] + new + s[j:]


cut(r"\begin{abstract}", r"\end{abstract}", r"""\begin{abstract}
Photo managers that group faces on the user's own device must update the groups as photos arrive, and users correct them
by hand. Greedy incremental clustering makes the people found depend on import order, and re-clustering from scratch
undoes the corrections. We study the face clusterer of Cove, a local-first photo manager, whose output is a function of the
set of faces and the set of must-link and cannot-link corrections: single linkage over core faces, an attach step and a
centroid merge. On simulated libraries whose people are disjoint from the tuning data, its accuracy without corrections is
within about one point of average linkage overall (ahead on clean photos, behind on low-resolution photos and, by 7 points,
on profile ones), and on web family photos (FIW) with no retuning it again ties average linkage. With corrections (three
simulated users, EdgeFace-S) it is within 0.003 F1 of constrained average linkage. It keeps every consistent correction
across the next import, where plain re-clustering keeps 20\% and re-applying keeps 73--96\%, and its read step is roughly an
order of magnitude faster than constrained average linkage on synthetic libraries of up to 50{,}000 faces. Recomputing from
the two sets, as any such design would, gives in simulation identical people on two devices (53\% and 31\% for a
frozen-label rule of our design), exact retraction and deletion, and corrections that keep about half their gain under a
different recogniser. For our clusterer the gain from corrections is gone by about one wrong click in twenty, while
re-applying and constrained average linkage degrade more gently, so a review-and-undo view is advisable. Only the clusterer
is in the application; corrections, devices and users are simulated.
""")

rep(r"an outside test on real family photos (FIW)", r"an outside test on web family photos (FIW)")
rep(r"\emph{Real family photos:} FIW", r"\emph{Web family photos:} FIW")
rep(r"30 libraries of real family photos with", r"30 libraries of web family photos with")
rep(r"\emph{Real family photos.} On FIW we changed nothing", r"\emph{Web family photos (FIW).} On FIW we changed nothing")
rep(r"\emph{Real family photos.} On the FIW libraries", r"\emph{Web family photos (FIW).} On the FIW libraries")

rep(r"\textbf{Test.} Every method runs in 5 shuffled orders.", r"\textbf{Test.} On the LFW libraries every method runs in 5 shuffled orders (on FIW, order-dependent methods 5, the others 3).")

# fair-tuning trim
rep(r"""(581 configurations) did not help them: average linkage scored 0.9849 overall against 0.9857 with the coarse grid, and none
moved by more than 0.0021. Giving ours only 51 random grid points (5 draws) scores 0.9809 to 0.9857 (mean 0.9836) against
0.9854 for its full grid.""", r"""(581 configurations) did not help them (average linkage 0.9849 against 0.9857; none moved by more than 0.0021), and giving
ours only 51 random grid points scores 0.9809 to 0.9857 (mean 0.9836) against 0.9854.""")

# FIW paragraph: attach + MBF shorter
rep(r"""MobileFaceNet gives the same picture (ours 0.783, average linkage 0.782, $+0.0014$,
$[-0.0020,+0.0048]$; re-tuned $-0.0042$, $[-0.0092,+0.0010]$).""", r"""Without the attach step ours scores 0.783. MobileFaceNet agrees (ours 0.783, average linkage 0.782; re-tuned
$-0.0042$, $[-0.0092,+0.0010]$).""")

# sweep paragraph
cut(r"This agrees with the error-rate sweep", r"\emph{Web family photos (FIW).} On the FIW libraries", r"""This agrees with the error-rate sweep (casual user, wrong ``same person'' clicks with probability $p$, 95\% paired-bootstrap
intervals): the gain of ours over discarding corrections is $+0.0065$ at $p=0$, $+0.0034$ at 0.02 ($[+0.0015,+0.0054]$),
$+0.0009$ at 0.05 and $+0.0010$ at 0.10 (intervals include zero), and $-0.0057$ at 0.20 ($[-0.0085,-0.0030]$). Re-applying stays
positive up to 0.20 ($+0.0039$, $+0.0037$, $+0.0025$ at 0.05, 0.10, 0.20) and constrained average linkage up to 0.10 ($+0.0028$,
$+0.0027$; $-0.0009$ at 0.20, interval includes zero), so our hard constraints are the least forgiving, probably because one
wrong merge joins whole groups of faces. For our clusterer, corrections should therefore be shown and removable.

""")

# scale trim
rep(r"""Adding all faces to the clusterer (flat FAISS index) in batches of 64 took 8\,s at
8{,}290 and 316\,s at 49{,}740 faces, longer than any baseline's read, so at this size the quadratic index build, not the read,
dominates and an incremental or approximate index would replace it.""", r"""Adding all faces to the flat FAISS index in batches of 64 took 8\,s at 8{,}290 and 316\,s at 49{,}740 faces
(quadratic, not optimised), so there the index build, not the read, dominates.""")

# discussion
cut(r"\textbf{What the results show.}", r"\textbf{Scope and next steps.}", r"""\textbf{What the results show.} Order-invariant people, corrections that persist across imports and accuracy within 0.003 F1 of
constrained average linkage (three simulated users, EdgeFace-S) come from well-understood parts, with a much cheaper read step
(9 to 15 times at 50{,}000 synthetic faces) and, over the frozen rule, device agreement, exact retraction and freedom to revise
earlier groupings. These properties follow from recomputing the groups from the sets, so any such design shares them. On the LFW
libraries all accuracy differences are small because most methods already score about 0.99; on FIW, at about 0.78, ours still
only ties average linkage. For our clusterer the gain from corrections is clear up to about two wrong clicks in a hundred
($+0.0034$, $[+0.0015,+0.0054]$), small at five to ten and negative at twenty, whereas re-applying and constrained average
linkage stay positive to ten; a review-and-undo view (cheap, since retraction is exact) is therefore advisable, though we did
not test one.

""")

rep(r"""Corrections help
less as wrong clicks grow, so they should come with a visible, removable list.""", r"""For our clusterer corrections help
less as wrong clicks grow, so they should come with a visible, removable list.""")
open(p, "w", encoding="utf8").write(s)

vp = r"D:\wincode\Major-Project\evaluation\verify_paper_numbers.py"
v = open(vp, encoding="utf8").read()
if "exp25 reapply p=0.05" not in v:
    add = '''
chk("exp25 ours gain CI lo p=0.02", 0.0015, t["0.02|ours"]["gain_ci95"][0], 4)
chk("exp25 ours gain CI hi p=0.02", 0.0054, t["0.02|ours"]["gain_ci95"][1], 4)
chk("exp25 reapply p=0.05", 0.0039, t["0.05|ours+reapply"]["gain_over_discarding"], 4)
chk("exp25 reapply p=0.1", 0.0037, t["0.1|ours+reapply"]["gain_over_discarding"], 4)
chk("exp25 reapply p=0.2", 0.0025, t["0.2|ours+reapply"]["gain_over_discarding"], 4)
chk("exp25 c-avg p=0.05", 0.0028, t["0.05|c-avg"]["gain_over_discarding"], 4)
chk("exp25 c-avg p=0.1", 0.0027, t["0.1|c-avg"]["gain_over_discarding"], 4)
chk("exp31 FIW ours no-attach F1", 0.783, At["table"]["Ours, no attach"]["B3_F1"], 3)
'''
    v = v.replace('print(f"\\n{n_ok} ok, {bad} mismatch")', add + '\nprint(f"\\n{n_ok} ok, {bad} mismatch")')
    open(vp, "w", encoding="utf8").write(v)
print("round-9 edits applied")
