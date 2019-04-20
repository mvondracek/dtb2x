"""
dtb2x
Simple and easy to use DTB to XLSX (and CSV) format converter.
Martin Vondracek <vondracek.mar@gmail.com>
2019
"""

import csv
import logging
import re
from abc import ABC, abstractmethod
from typing import List, TextIO, Union, Optional

from openpyxl import Workbook


logger = logging.getLogger(__name__)


class Dtb2CsvError(Exception):
    """Base class for exceptions in dtb2x module."""

    def __init__(self, message):
        self.message = message


class Group:
    """Group contains teams. Group is a top-level record in DTB file. """

    def __init__(self, name: str, note: str):
        self.name = name
        self.note = note

    def __repr__(self):
        return 'Group({}, {})'.format(self.name, self.note)

    def to_list(self) -> List:
        return [self.name, self.note]

    @classmethod
    def header(cls) -> List[str]:
        return ['Název, Oddíl', 'Poznámka, Oddíl']


class Team:
    """Team belongs to a single group and contains players."""

    def __init__(self, name: str, note: str, group: Group):
        self.name = name
        self.note = note
        self.group = group

    def __repr__(self):
        return 'Team({}, {}, {})'.format(self.name, self.note, self.group)

    def to_list(self) -> List:
        return self.group.to_list() + [self.name, self.note]

    @classmethod
    def header(cls) -> List[str]:
        return ['Název, Družstvo', 'Poznámka, Družstvo']


class Player:
    """Player belongs to a single team."""

    def __init__(self, registration_number: str, name: str, surname: str, date_of_birth: str, note: str, team: Team):
        # TODO MV: In case we would like to do some validations, `registration_number` could be int and `date_of_birth`
        # could be datetime.date.
        self.registration_number = registration_number
        self.name = name
        self.surname = surname
        self.date_of_birth = date_of_birth
        self.note = note
        self.team = team

    def __repr__(self):
        return 'Player({}, {}, {}, {}, {}, {},)'.format(
            self.registration_number, self.name, self.surname, self.date_of_birth, self.note, self.team
        )

    def to_list(self) -> List:
        return self.team.to_list() + [
            self.registration_number,
            self.name,
            self.surname,
            self.date_of_birth,
            self.note
        ]

    @classmethod
    def header(cls) -> List[str]:
        return ['Reg. číslo, Hráč', 'Jméno, Hráč', 'Příjmení, Hráč', 'Datum nar., Hráč', 'Poznámka, Hráč']


class DtbReader:
    """
    Reader of DTB format capable of instantiating individual DTB entities from input text.
    """

    # Spaces in the beginning of `name` and `registration_number` are discarded
    GROUP_RE_STRICT = re.compile(r'^((?P<name>[^\t]*) )?- (?P<note>.+)?\n$')
    GROUP_RE_LOOSE = re.compile(r'^((?P<name>[^\t]*) )?- ?(?P<note>.+)?\n$')
    TEAM_RE_STRICT = re.compile(r'^\t((?P<name>[^\t]*) )?- (?P<note>.+)?\n$')
    TEAM_RE_LOOSE = re.compile(r'^\t((?P<name>[^\t]*) )?- ?(?P<note>.+)?\n$')
    PLAYER_RE_STRICT = re.compile(
        r'^\t\t((?P<registration_number>\d*) )?- (?P<surname>[^ ,]+)? (?P<name>[^,]+)?, (?P<date_of_birth>[\d.]+)?'
        r' +, (?P<note>.+)?\n$')
    PLAYER_RE_LOOSE = re.compile(
        r'^\t\t((?P<registration_number>\d*) )?- (?P<surname>[^ ,]+)? (?P<name>[^,]+)?,? ?(?P<date_of_birth>[\d.]+)?'
        r' +,? ?(?P<note>.+)?\n$')

    def __init__(self):
        self.current_group = None  # type:Optional[Group]
        self.current_team = None  # type:Optional[Team]

    def read(self, line: str, strict: bool = True) -> Union[Group, Team, Player]:
        """
        :param line: Single line of DTB file.
        :param strict: Convert using strict mode for reading DTB file and validation of its format. When strict mode is
        enabled, trying to convert DTB file containing format mistakes raises Exceptions. If strict mode is disabled,
        the reader tries to tolerate small formatting mistakes like missing spaces and missing commas.
        :return: Read DTB entity from DTB file.

        :raises DtbReader.InvalidDtbFileError: If `line` is not a valid DTB entity, therefore the input file is invalid.
        """
        if strict:
            group_re = self.GROUP_RE_STRICT
            team_re = self.TEAM_RE_STRICT
            player_re = self.PLAYER_RE_STRICT
        else:
            group_re = self.GROUP_RE_LOOSE
            team_re = self.TEAM_RE_LOOSE
            player_re = self.PLAYER_RE_LOOSE

        group_match = group_re.fullmatch(line)
        if group_match:
            group = Group(group_match.group('name'), group_match.group('note'))
            self.current_group = group
            self.current_team = None
            logger.info('DtbReader: read Group={}'.format(group))
            return group

        team_match = team_re.fullmatch(line)
        if team_match:
            if self.current_group is None:
                error_message = 'DtbReader: Team without Group:`{}`'.format(line)
                logger.error(error_message)
                raise DtbReader.InvalidDtbFileError(error_message)
            team = Team(team_match.group('name'), team_match.group('note'), self.current_group)
            self.current_team = team
            logger.info('DtbReader: read Team={}'.format(team))
            return team

        player_match = player_re.fullmatch(line)
        if player_match:
            if self.current_team is None:
                error_message = 'DtbReader: Player without team:`{}`'.format(line)
                logger.error(error_message)
                raise DtbReader.InvalidDtbFileError(error_message)
            player = Player(player_match.group('registration_number'), player_match.group('name'),
                            player_match.group('surname'), player_match.group('date_of_birth'),
                            player_match.group('note'), self.current_team)
            logger.info('DtbReader: read Player={}'.format(player))
            return player

        error_message = 'DtbReader: Unknown line type:`{}`'.format(line)
        logger.error(error_message)
        raise DtbReader.InvalidDtbFileError(error_message)

    class InvalidDtbFileError(Dtb2CsvError):
        def __repr__(self):
            return 'DtbReader.InvalidDtbFileError({})'.format(self.message)


class Converter(ABC):
    """
    Abstract base class for DTB converters.
    """
    @staticmethod
    @abstractmethod
    def newline() -> Union[str, None]:
        """
        Newline parameter for opening output file with `open` call.
        """
        pass

    @staticmethod
    @abstractmethod
    def convert(input_file: TextIO, output_file: TextIO, strict: bool = True):
        """
        :param input_file: Input text file in DTB format
        :param output_file: Output text file.
        :param strict: Convert using strict mode for reading DTB file and validation of its format. When strict mode is
            enabled, trying to convert DTB file containing format mistakes raises Exceptions. If strict mode is
            disabled, the reader tries to tolerate small formatting mistakes like missing spaces and missing commas.

        :raises DtbReader.InvalidDtbFileError: If `line` is not a valid DTB entity, therefore the input file is invalid.
        """
        pass


class ConverterCsv(Converter):
    """
    DTB converter to CSV.
    """
    @staticmethod
    def newline() -> Union[str, None]:
        return ''

    @staticmethod
    def convert(dtb_input: TextIO, csv_output: TextIO, strict: bool = True):
        """
        :param dtb_input: Input text file in DTB format
        :param csv_output: Output text file in CSV format.
            CSV file should be opened with <code>newline=''</code>, see https://docs.python.org/3.5/library/csv.html#id3
        :param strict: Convert using strict mode for reading DTB file and validation of its format. When strict mode is
            enabled, trying to convert DTB file containing format mistakes raises Exceptions. If strict mode is
            disabled, the reader tries to tolerate small formatting mistakes like missing spaces and missing commas.

        :raises DtbReader.InvalidDtbFileError: If `line` is not a valid DTB entity, therefore the input file is invalid.
        """
        reader = DtbReader()
        # NOTE MV: Microsoft Excel expects delimiter based on regional settings
        writer = csv.writer(csv_output, dialect=csv.excel, delimiter=';')

        # write custom CSV header
        header = Group.header() + Team.header() + Player.header()
        writer.writerow(header)

        for line in dtb_input:
            entity = reader.read(line, strict=strict)  # entity is Group, Team, or Player
            if entity is not None:
                csv_line = entity.to_list()
                # make sure all lines in csv have the same number of columns
                if len(csv_line) < len(header):
                    csv_line += [None]*(len(header) - len(csv_line))
                writer.writerow(csv_line)


class ConverterXlsx(Converter):
    """
    DTB converter to XLSX.
    """

    @staticmethod
    def newline() -> Union[str, None]:
        return None

    @staticmethod
    def convert(dtb_input: TextIO, xlsx_output: TextIO, strict: bool = True):
        """
        :param dtb_input: Input text file in DTB format
        :param xlsx_output: Output text file in XLSX format.
        :param strict: Convert using strict mode for reading DTB file and validation of its format. When strict mode is
            enabled, trying to convert DTB file containing format mistakes raises Exceptions. If strict mode is
            disabled, the reader tries to tolerate small formatting mistakes like missing spaces and missing commas.

        :raises DtbReader.InvalidDtbFileError: If `line` is not a valid DTB entity, therefore the input file is invalid.
        """
        reader = DtbReader()
        workbook = Workbook()
        worksheet = workbook.active  # grab the active worksheet
        worksheet.title = "DTB"
        worksheet.freeze_panes = 'A2'
        # write custom header
        worksheet.append(Group.header() + Team.header() + Player.header())
        for line in dtb_input:
            entity = reader.read(line, strict=strict)  # entity is Group, Team, or Player
            if entity is not None:
                worksheet.append(entity.to_list())
        workbook.save(xlsx_output.name)
