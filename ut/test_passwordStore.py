import os
from unittest import TestCase
from pw_store import ECNotFoundException, Entry, EntryContainer, PasswordStore


class TestPasswordStore(TestCase):
    def setUp(self):
        self.test_xml_filename = os.path.join("ut", "store.xml")
        with open(self.test_xml_filename, "rb") as f:
            raw_xml = f.read()
        self.cut = PasswordStore(raw_xml)

    def test_get_root(self):
        root = self.cut.get_root()
        self.assertIsNotNone(root)

    def test_get_container_by_path(self):
        root = self.cut.get_root()
        lvl1 = EntryContainer()
        lvl2 = EntryContainer()
        lvl3 = EntryContainer()
        lvl2.add_container(lvl3, "lvl3")
        lvl1.add_container(lvl2, "lvl2")
        root.add_container(lvl1, "lvl1")
        self.assertEqual(lvl1, self.cut.get_container_by_path("/lvl1"))
        self.assertEqual(lvl2, self.cut.get_container_by_path("/lvl1/lvl2"))
        self.assertEqual(lvl3, self.cut.get_container_by_path("/lvl1/lvl2/lvl3"))

    def test_invalid_container_path(self):
        with self.assertRaises(ECNotFoundException):
            self.cut.get_container_by_path("/Something/Not/there")

    def test_get_entry_by_path(self):
        new_cont = EntryContainer()
        entry = Entry()
        new_cont.add_entry(entry, "Entry1")
        self.cut.add_container(new_cont, "A New Beginning", "/")
        self.assertEqual(("Entry1", entry), self.cut.get_entry_by_path("/A New Beginning/Entry1"))

    def match_entries(self, cont1, cont2):
        self.assertEqual(cont1.get_entry_count(), cont2.get_entry_count())
        for k, e1 in cont1.get_entries():
            try:
                e2 = cont2.get_entry(k)
                self.assertEqual(e1.get_username(), e2.get_username())
                self.assertEqual(e1.get_password(), e2.get_password())
                self.assertEqual(e1.get_url(), e2.get_url())
            except ECNotFoundException:
                self.fail("Entry {0} not found in both containers.".format(k))

    def match_containers(self, cont1, cont2):
        self.assertEqual(cont1.get_container_count(),
                         cont2.get_container_count())
        self.match_entries(cont1, cont2)
        for k, c1 in cont1.get_containers():
            try:
                c2 = cont2.get_container(k)
                self.match_containers(c1, c2)
            except ECNotFoundException:
                self.fail("Container {0} not found in both containers.".format(k))

    def test_roundtrip_xml_serialization(self):
        serialized_xml = self.cut.serialize_to_xml()
        store = PasswordStore(serialized_xml)

        self.match_containers(self.cut.get_root(), store.get_root())

