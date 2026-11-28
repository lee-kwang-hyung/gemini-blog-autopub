import unittest
from qa_and_sanitizer import run_triple_qa
from review_gate import assess
class Review(unittest.TestCase):
    def test_card(self):
        body = "<p>여행 공항 " + "점검 " * 460 + "</p><a href='https://trip.com/hotels'><img src='x'>예약</a><!--a<!--b-->--> "
        r = run_triple_qa("여행 공항", body, "REVIEW", travel_only=True)
        self.assertTrue(r["ok"]); self.assertNotIn("예약",r["html"]); self.assertNotIn("--",r["html"])
    def test_short(self):
        self.assertTrue(run_triple_qa("여행 공항","공항 여행", "REVIEW")["draft"])
    def test_mismatch(self):
        self.assertTrue(run_triple_qa("윈도우 지원 종료","윈도우 지원 종료 "*220,"REVIEW",travel_only=True)["draft"])
        self.assertTrue(run_triple_qa("항공권 이름 변경","공항 수하물 "*240,"REVIEW",travel_only=True)["draft"])
    def test_gate(self):
        url="https://genesislkh21.blogspot.com/2026/11/a.html"
        row=dict(canonical=url,google_canonical=url,status="LIVE",chars=1300,travel_match=True,page_clean=True,indexed=True,snippet_clean=True,checked_at="2026-11-28",inspection_evidence="inspection",snippet_evidence="snippet")
        self.assertEqual(assess({"posts":[row]*15})[0],1)
        self.assertEqual(assess({"posts":[dict(row,snippet_clean=None)]})[0],0)
        self.assertTrue(assess({})[1])
