import csv
import io
from unittest import TestCase

from dtb2csv import DtbReader, Group, Team, Player, convert, main


class TestDtbReader(TestCase):
    def setUp(self):
        self.reader = DtbReader()

    def test_read_one_player(self):
        group = self.reader.read('group_name - group_note\n')
        self.assertEqual(group.name, 'group_name')
        self.assertEqual(group.note, 'group_note')

        team = self.reader.read('	team_name - team_note\n')
        self.assertEqual(team.name, 'team_name')
        self.assertEqual(team.note, 'team_note')
        self.assertEqual(team.group, group)

        player = self.reader.read('		123456789 - player_surname player_name, 01.01.1900 , player_note\n')
        self.assertEqual(player.name, 'player_name')
        self.assertEqual(player.surname, 'player_surname')
        self.assertEqual(player.date_of_birth, '01.01.1900')
        self.assertEqual(player.registration_number, '123456789')
        self.assertEqual(player.note, 'player_note')
        self.assertEqual(player.team, team)

    def test_read_more_players(self):
        group = self.reader.read('group_name - group_note\n')
        team = self.reader.read('	team_name - team_note\n')

        player = self.reader.read('		1 - player_surname player_name, 01.01.1900 , player_note\n')
        self.assertEqual(player.team, team)
        self.assertEqual(player.team.group, group)
        player = self.reader.read('		2 - player_surname player_name, 01.01.1900 , player_note\n')
        self.assertEqual(player.team, team)
        self.assertEqual(player.team.group, group)

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


class TestConvert(TestCase):
    def test_convert(self):
        input_file = io.StringIO(
            'group_name - group_note\n' +
            '	team_name - team_note\n' +
            '		123456789 - player_surname player_name, 01.01.1900 , player_note\n',
            newline=None)
        output_expected = (
            'group_name;group_note\n'
            'group_name;group_note;team_name;team_note\n'
            'group_name;group_note;team_name;team_note;123456789;player_name;player_surname;01.01.1900;'
            'player_note\n')
        output_file = io.StringIO(newline=None)
        convert(input_file, output_file)
        self.assertEqual(output_file.getvalue(), output_expected)

    def test_basic(self):
        input_file = io.StringIO(
            'group_name - \n'
            '	team_name - \n'
            '		-  player_name,  , \n',
            newline=None)
        output_expected = (
            'group_name;\n'
            'group_name;;team_name;\n'
            'group_name;;team_name;;;player_name;;;\n')
        output_file = io.StringIO(newline=None)
        convert(input_file, output_file)
        self.assertEqual(output_file.getvalue(), output_expected)

    def test_empty(self):
        input_file = io.StringIO(
            '- \n'
            '	- \n'
            '		-  ,  , \n',
            newline=None)
        output_expected = (
            ';\n'
            ';;;\n'
            ';;;;;;;;\n')
        output_file = io.StringIO(newline=None)
        convert(input_file, output_file)
        self.assertEqual(output_file.getvalue(), output_expected)

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
            'group1;group_note\n'
            'group2;group_note\n'
            'group2;group_note;team2;team_note\n'
            'group3;group_note\n'
            'group3;group_note;team3;team_note\n'
            'group3;group_note;team3;team_note;123456789;player_name;player_surname;01.01.2000;player_note\n')
        output_file = io.StringIO(newline=None)
        convert(input_file, output_file)
        self.assertEqual(output_file.getvalue(), output_expected)

    def test_full(self):
        input_file = io.StringIO(
            'group_name - group_note\n'
            '	team_name - team_note\n'
            '		123456789 - player_surname player_name, 01.01.2000 , player_note\n',
            newline=None)
        output_expected = (
            'group_name;group_note\n'
            'group_name;group_note;team_name;team_note\n'
            'group_name;group_note;team_name;team_note;123456789;player_name;player_surname;01.01.2000;player_note\n')
        output_file = io.StringIO(newline=None)
        convert(input_file, output_file)
        self.assertEqual(output_file.getvalue(), output_expected)

    def test_invalid_file_team_wo_group(self):
        input_file = io.StringIO(
            '	team1 - team_note\n'
            'group2 - group_note\n'
            '	team2 - team_note\n'
            '		123456789 - player_surname player_name, 01.01.2000 , player_note',
            newline=None)
        output_file = io.StringIO(newline=None)
        with self.assertRaises(DtbReader.InvalidDtbFileError):
            convert(input_file, output_file)

    def test_invalid_file_player_wo_team_and_group(self):
        input_file = io.StringIO(
            '		123456789 - player_surname player1, 01.01.2000 , player_note\n'
            'group2 - group_note\n'
            '	team2 - team_note\n'
            '		123456789 - player_surname player2, 01.01.2000 , player_note',
            newline=None)
        output_file = io.StringIO(newline=None)
        with self.assertRaises(DtbReader.InvalidDtbFileError):
            convert(input_file, output_file)

    def test_invalid_file_player_wo_team(self):
        input_file = io.StringIO(
            'group1 - group_note\n'
            '		123456789 - player_surname player1, 01.01.2000 , player_note',
            newline=None)
        output_file = io.StringIO(newline=None)
        with self.assertRaises(DtbReader.InvalidDtbFileError):
            convert(input_file, output_file)

