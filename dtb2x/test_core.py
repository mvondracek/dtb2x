"""
dtb2x
Simple and and easy to use DTB to XLSX (and CSV) format converter.
Martin Vondracek <vondracek.mar@gmail.com>
2019
"""

import io
from unittest import TestCase

from .core import DtbReader, ConverterCsv


class TestDtbReader(TestCase):
    def setUp(self):
        self.reader = DtbReader()

    def test_read_one_player(self):
        group = self.reader.read('group_name - group_note\n')
        self.assertEqual('group_name', group.name)
        self.assertEqual('group_note', group.note)

        team = self.reader.read('	team_name - team_note\n')
        self.assertEqual('team_name', team.name)
        self.assertEqual('team_note', team.note)
        self.assertEqual(group, team.group)

        player = self.reader.read('		123456789 - player_surname player_name, 01.01.1900 , player_note\n')
        self.assertEqual('player_name', player.name)
        self.assertEqual('player_surname', player.surname)
        self.assertEqual('01.01.1900', player.date_of_birth)
        self.assertEqual('123456789', player.registration_number)
        self.assertEqual('player_note', player.note)
        self.assertEqual(team, player.team)

    def test_player_registration_number_as_string(self):
        group = self.reader.read('group_name - group_note\n')
        self.assertEqual('group_name', group.name)
        self.assertEqual('group_note', group.note)

        team = self.reader.read('	team_name - team_note\n')
        self.assertEqual('team_name', team.name)
        self.assertEqual('team_note', team.note)
        self.assertEqual(group, team.group)

        player = self.reader.read('		000000001 - player_surname player_name, 01.01.1900 , player_note\n')
        self.assertEqual('player_name', player.name)
        self.assertEqual('player_surname', player.surname)
        self.assertEqual('01.01.1900', player.date_of_birth)
        self.assertEqual('000000001', player.registration_number)
        self.assertEqual('player_note', player.note)
        self.assertEqual(team, player.team)

    def test_group_strip_whitespace(self):
        group = self.reader.read('group_name - group_note     \n')
        self.assertEqual('group_name', group.name)
        self.assertEqual('group_note     ', group.note)

        group = self.reader.read('group_name -     group_note\n')
        self.assertEqual('group_name', group.name)
        self.assertEqual('    group_note', group.note)

        group = self.reader.read('group_name -     group_note     \n')
        self.assertEqual('group_name', group.name)
        self.assertEqual('    group_note     ', group.note)

        group = self.reader.read('group_name     - group_note\n')
        self.assertEqual('group_name    ', group.name)
        self.assertEqual('group_note', group.note)

        group = self.reader.read('group_name     - group_note     \n')
        self.assertEqual('group_name    ', group.name)
        self.assertEqual('group_note     ', group.note)

        group = self.reader.read('group_name     -     group_note     \n')
        self.assertEqual('group_name    ', group.name)
        self.assertEqual('    group_note     ', group.note)

    def test_read_more_players(self):
        group = self.reader.read('group_name - group_note\n')
        team = self.reader.read('	team_name - team_note\n')

        player = self.reader.read('		1 - player_surname player_name, 01.01.1900 , player_note\n')
        self.assertEqual(team, player.team)
        self.assertEqual(group, player.team.group)
        player = self.reader.read('		2 - player_surname player_name, 01.01.1900 , player_note\n')
        self.assertEqual(team, player.team)
        self.assertEqual(group, player.team.group)

    def test_read_more_teams(self):
        group = self.reader.read('group_name - group_note\n')
        team_1 = self.reader.read('	team_name_1 - team_note\n')
        player_1 = self.reader.read('		1 - player_surname player_name, 01.01.1900 , player_note\n')
        self.assertEqual(player_1.team, team_1)
        self.assertEqual(team_1.group, group)
        team_2 = self.reader.read('	team_name_2 - team_note\n')
        player_2 = self.reader.read('		1 - player_surname player_name, 01.01.1900 , player_note\n')
        self.assertEqual(player_2.team, team_2)
        self.assertEqual(team_2.group, group)


class TestConverterCsv(TestCase):
    def setUp(self):
        self.CSV_HEADER = \
            'Název, Oddíl;Poznámka, Oddíl;' \
            'Název, Družstvo;Poznámka, Družstvo;' \
            'Reg. číslo, Hráč;Jméno, Hráč;Příjmení, Hráč;Datum nar., Hráč;Poznámka, Hráč\n'

    def test_convert(self):
        input_file = io.StringIO(
            'group_name - group_note\n' +
            '	team_name - team_note\n' +
            '		123456789 - player_surname player_name, 01.01.1900 , player_note\n',
            newline=None)
        output_expected = (
            self.CSV_HEADER +
            'group_name;group_note\n'
            'group_name;group_note;team_name;team_note\n'
            'group_name;group_note;team_name;team_note;123456789;player_name;player_surname;01.01.1900;'
            'player_note\n')
        output_file = io.StringIO(newline=None)
        ConverterCsv.convert(input_file, output_file)
        self.assertEqual(output_expected, output_file.getvalue())

    def test_player_registration_number_as_string(self):
        input_file = io.StringIO(
            'group_name - group_note\n' +
            '	team_name - team_note\n' +
            '		000000001 - player_surname player_name, 01.01.1900 , player_note\n',
            newline=None)
        output_expected = (
            self.CSV_HEADER +
            'group_name;group_note\n'
            'group_name;group_note;team_name;team_note\n'
            'group_name;group_note;team_name;team_note;000000001;player_name;player_surname;01.01.1900;'
            'player_note\n')
        output_file = io.StringIO(newline=None)
        ConverterCsv.convert(input_file, output_file)
        self.assertEqual(output_expected, output_file.getvalue())

    def test_loose_no_strict(self):
        input_file = io.StringIO(
            'group_name -\n' +
            '	team_name -\n' +
            '		123456789 - player_surname1 player_name1, 01.01.1900 ,\n' +
            '		123456789 - player_surname2 player_name2, 01.01.1900     ,\n' +
            '		- player_surname3 player_name3 \n' +
            '		- player_surname4 player_name4, , \n',
            newline=None)
        output_expected = (
            self.CSV_HEADER +
            'group_name;\n'
            'group_name;;team_name;\n'
            'group_name;;team_name;;123456789;player_name1;player_surname1;01.01.1900;\n'
            'group_name;;team_name;;123456789;player_name2;player_surname2;01.01.1900;\n'
            'group_name;;team_name;;;player_name3;player_surname3;;\n'
            'group_name;;team_name;;;player_name4;player_surname4;;\n')
        output_file = io.StringIO(newline=None)
        ConverterCsv.convert(input_file, output_file, strict=False)
        self.assertEqual(output_expected, output_file.getvalue())

    def test_basic_surname(self):
        input_file = io.StringIO(
            'group_name - \n'
            '	team_name - \n'
            '		-  player_name,  , \n',
            newline=None)
        output_expected = (
            self.CSV_HEADER +
            'group_name;\n'
            'group_name;;team_name;\n'
            'group_name;;team_name;;;player_name;;;\n')
        output_file = io.StringIO(newline=None)
        ConverterCsv.convert(input_file, output_file)
        self.assertEqual(output_expected, output_file.getvalue())

    def test_basic_surname_name(self):
        input_file = io.StringIO(
            'group_name - \n'
            '	team_name - \n'
            '		- player_surname player_name,  , \n',
            newline=None)
        output_expected = (
            self.CSV_HEADER +
            'group_name;\n'
            'group_name;;team_name;\n'
            'group_name;;team_name;;;player_name;player_surname;;\n')
        output_file = io.StringIO(newline=None)
        ConverterCsv.convert(input_file, output_file)
        self.assertEqual(output_expected, output_file.getvalue())

    def test_basic_name(self):
        input_file = io.StringIO(
            'group_name - \n'
            '	team_name - \n'
            '		-  player_name,  , \n',
            newline=None)
        output_expected = (
            self.CSV_HEADER +
            'group_name;\n'
            'group_name;;team_name;\n'
            'group_name;;team_name;;;player_name;;;\n')
        output_file = io.StringIO(newline=None)
        ConverterCsv.convert(input_file, output_file)
        self.assertEqual(output_expected, output_file.getvalue())

    def test_empty(self):
        input_file = io.StringIO(
            '- \n'
            '	- \n'
            '		-  ,  , \n',
            newline=None)
        output_expected = (
            self.CSV_HEADER +
            ';\n'
            ';;;\n'
            ';;;;;;;;\n')
        output_file = io.StringIO(newline=None)
        ConverterCsv.convert(input_file, output_file)
        self.assertEqual(output_expected, output_file.getvalue())

    def test_partial(self):
        input_file = io.StringIO(
            'group1 - group_note\n'
            'group2 - group_note\n'
            '	team2 - team_note\n'
            'group3 - group_note\n'
            '	team3 - team_note\n'
            '		123456789 - player_surname player_name, 01.01.2000 , player_note\n',
            newline=None)
        output_expected = (
            self.CSV_HEADER +
            'group1;group_note\n'
            'group2;group_note\n'
            'group2;group_note;team2;team_note\n'
            'group3;group_note\n'
            'group3;group_note;team3;team_note\n'
            'group3;group_note;team3;team_note;123456789;player_name;player_surname;01.01.2000;player_note\n')
        output_file = io.StringIO(newline=None)
        ConverterCsv.convert(input_file, output_file)
        self.assertEqual(output_expected, output_file.getvalue())

    def test_full(self):
        input_file = io.StringIO(
            'group_name - group_note\n'
            '	team_name - team_note\n'
            '		123456789 - player_surname player_name, 01.01.2000 , player_note\n',
            newline=None)
        output_expected = (
            self.CSV_HEADER +
            'group_name;group_note\n'
            'group_name;group_note;team_name;team_note\n'
            'group_name;group_note;team_name;team_note;123456789;player_name;player_surname;01.01.2000;player_note\n')
        output_file = io.StringIO(newline=None)
        ConverterCsv.convert(input_file, output_file)
        self.assertEqual(output_expected, output_file.getvalue())

    def test_invalid_file_team_wo_group(self):
        input_file = io.StringIO(
            '	team1 - team_note\n'
            'group2 - group_note\n'
            '	team2 - team_note\n'
            '		123456789 - player_surname player_name, 01.01.2000 , player_note',
            newline=None)
        output_file = io.StringIO(newline=None)
        with self.assertRaises(DtbReader.InvalidDtbFileError):
            ConverterCsv.convert(input_file, output_file)

    def test_invalid_file_player_wo_team_and_group(self):
        input_file = io.StringIO(
            '		123456789 - player_surname player1, 01.01.2000 , player_note\n'
            'group2 - group_note\n'
            '	team2 - team_note\n'
            '		123456789 - player_surname player2, 01.01.2000 , player_note',
            newline=None)
        output_file = io.StringIO(newline=None)
        with self.assertRaises(DtbReader.InvalidDtbFileError):
            ConverterCsv.convert(input_file, output_file)

    def test_invalid_file_player_wo_team(self):
        input_file = io.StringIO(
            'group1 - group_note\n'
            '		123456789 - player_surname player1, 01.01.2000 , player_note',
            newline=None)
        output_file = io.StringIO(newline=None)
        with self.assertRaises(DtbReader.InvalidDtbFileError):
            ConverterCsv.convert(input_file, output_file)
