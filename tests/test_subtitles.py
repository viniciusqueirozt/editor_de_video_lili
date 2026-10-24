import unittest
from lili.core import EditorError,uid
from lili.subtitles import parse_srt,to_srt,validate_captions
class SubtitleTests(unittest.TestCase):
    def test_srt_bom_crlf_multiline_roundtrip(self):
        captions=parse_srt("\ufeff1\r\n00:00:00,250 --> 00:00:01,500\r\nOlá, Cora!\r\nMais uma linha\r\n\r\n2\r\n00:00:02,000 --> 00:00:03,100\r\nTchau")
        self.assertEqual(captions[0]['start'],.25)
        restored=parse_srt(to_srt(captions))
        self.assertEqual([(c['start'],c['end'],c['text']) for c in captions],[(c['start'],c['end'],c['text']) for c in restored])
    def test_invalid_overlap_size_and_timestamps_are_rejected(self):
        for value in ('1\n00:99:00,000 --> 00:00:01,000\nx','bad','1\n00:00:01,000 --> 00:00:00,000\nx','x'*1000001):
            with self.assertRaises(EditorError):parse_srt(value)
        for rows in ([{'start':0,'end':1,'text':'a'},{'start':.5,'end':2,'text':'b'}],[{'start':0,'end':1,'text':''}],[{'start':True,'end':1,'text':'a'}]):
            with self.assertRaises(EditorError):validate_captions(rows)
    def test_duplicate_ids_and_markup_stay_plain(self):
        identity=uid();row={'id':identity,'start':0,'end':1,'text':'<b>literal</b>'}
        self.assertEqual(validate_captions([row])[0]['text'],row['text'])
        with self.assertRaises(EditorError):validate_captions([row,{**row,'start':2,'end':3}])
