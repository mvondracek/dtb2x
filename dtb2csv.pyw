#! /usr/bin/env python
import csv
import logging
import os
import re
import sys
import tkinter as tk
import warnings
from enum import Enum, unique
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import showerror
from typing import List, TextIO, Union

PROGRAM_NAME = 'dtb2csv'
PROGRAM_DESCRIPTION = 'Simple single-purpose DTB to CSV format converter.'
__version__ = '0.1.0'
__author__ = 'Martin Vondracek'
__email__ = 'vondracek.mar@gmail.com'

logger = logging.getLogger(__name__)


class Dtb2CsvError(Exception):
    """Base class for exceptions in dtb2csv module."""

    def __init__(self, message):
        self.message = message


@unique
class ExitCode(Enum):
    """
    Exit codes. Some are inspired by sysexits.h.
    """
    EX_OK = 0
    """Program terminated successfully."""

    ARGUMENTS = 2
    """Incorrect or missing arguments provided."""

    KEYBOARD_INTERRUPT = 130
    """Program received SIGINT."""


class Group:
    """Group contains teams. Group is a top level record in DTB file. """

    def __init__(self, name: str, note: str):
        self.name = name
        self.note = note

    def __repr__(self):
        return 'Group({}, {})'.format(self.name, self.note)

    def to_list(self) -> List:
        return [self.name, self.note]


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


class DtbReader:
    # Spaces in the beginning of `name` and `registration_number` are discarded
    GROUP_RE = re.compile(r'^((?P<name>[^\t]*) )?- (?P<note>.+)?\n$')
    TEAM_RE = re.compile(r'^\t((?P<name>[^\t]*) )?- (?P<note>.+)?\n$')
    PLAYER_RE = re.compile(
        r'^\t\t((?P<registration_number>[^\t]*) )?- (?P<surname>.+)? (?P<name>.+)?, (?P<date_of_birth>.+)?'
        r' , (?P<note>.+)?\n$')

    def __init__(self):
        self.current_group = None  # type:Group
        self.current_team = None  # type:Team

    def read(self, line) -> Union[Group, Team, Player]:
        group_match = self.GROUP_RE.fullmatch(line)
        if group_match:
            group = Group(group_match.group('name'), group_match.group('note'))
            self.current_group = group
            self.current_team = None
            logger.info('DtbReader: read Group={}'.format(group))
            return group

        team_match = self.TEAM_RE.fullmatch(line)
        if team_match:
            if self.current_group is None:
                error_message = 'DtbReader: Team without Group:`{}`'.format(line)
                logger.error(error_message)
                raise DtbReader.InvalidDtbFileError(error_message)
            team = Team(team_match.group('name'), team_match.group('note'), self.current_group)
            self.current_team = team
            logger.info('DtbReader: read Team={}'.format(team))
            return team

        player_match = self.PLAYER_RE.fullmatch(line)
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


def convert(dtb_input: TextIO, csv_output: TextIO):
    reader = DtbReader()
    # NOTE MV: Microsoft Excel expects delimiter based on regional settings
    writer = csv.writer(csv_output, dialect=csv.excel, delimiter=';')
    for line in dtb_input:
        entity = reader.read(line)  # entity is Group, Team, or Player
        if entity is not None:
            writer.writerow(entity.to_list())


class Application:
    def __init__(self):
        self.root = tk.Tk()

        self.input_dtb_filepath = tk.StringVar()
        self.output_csv_filepath = tk.StringVar()

        self.root.title(PROGRAM_NAME)

        menu = tk.Menu(self.root)
        file_menu = tk.Menu(menu)
        file_menu.add_command(label="Select input DTB file...", command=self.ask_input_dtb_filepath)
        file_menu.add_command(label="Convert", command=self.convert)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.root.quit)
        menu.add_cascade(label="File", menu=file_menu)
        help_menu = tk.Menu(menu)
        help_menu.add_command(label="About " + PROGRAM_NAME, command=self.about)
        menu.add_cascade(label="Help", menu=help_menu)
        self.root.config(menu=menu)

        tk.Label(self.root, text="Input DTB file:").grid(row=0, column=0)
        tk.Entry(self.root, textvariable=self.input_dtb_filepath).grid(row=0, column=1)
        tk.Button(self.root, text='Browse...', command=self.ask_input_dtb_filepath).grid(row=0, column=2)

        tk.Button(self.root, text='Convert', command=self.convert).grid(row=2, column=0, columnspan=3)

    def ask_input_dtb_filepath(self):
        input_filepath = tk.filedialog.askopenfilename(
            title='Open DTB file',
            filetypes=(("DTB files", "*.dtb"), ("all files", "*.*"))
        )
        logger.debug('Selected input DTB filepath `{}`'.format(input_filepath))
        self.input_dtb_filepath.set(input_filepath)

    def ask_output_csv_filepath(self):
        input_filepath = self.input_dtb_filepath.get()
        if input_filepath:
            initial_file = os.path.splitext(os.path.basename(input_filepath))[0]
            initial_directory = os.path.dirname(input_filepath)
        else:
            initial_file = ''
            initial_directory = ''

        output_filepath = tk.filedialog.asksaveasfilename(
            title='Save CSV file',
            filetypes=(("CSV files", "*.csv"), ("all files", "*.*")),
            defaultextension='.csv',
            initialfile=initial_file,
            initialdir=initial_directory
        )
        logger.debug('Selected output CSV filepath `{}`'.format(output_filepath))
        self.output_csv_filepath.set(output_filepath)

    def convert(self):
        # form validation - input file
        input_filepath = self.input_dtb_filepath.get()
        if not input_filepath:
            logger.warning('No input DTB file selected.')
            tk.messagebox.showwarning('OK', 'Please select input DTB file first.')
            return
        if not os.path.isfile(input_filepath):
            warning_message = 'Selected input DTB file `{}` does not exist.'.format(input_filepath)
            logger.warning(warning_message)
            tk.messagebox.showwarning('OK', warning_message)
            return

        # output file
        self.ask_output_csv_filepath()
        output_filepath = self.output_csv_filepath.get()
        if not output_filepath:
            return  # user canceled `asksaveasfilename` dialog

        try:
            with open(input_filepath, mode='r') as dtb_file, \
                    open(output_filepath, mode='w') as csv_file:
                logger.info('Conversion started. input DTB = `{}`, output CSV = `{}`'
                            .format(input_filepath, output_filepath))
                convert(dtb_file, csv_file)

        except FileNotFoundError as e:
            logger.error(e)
            tk.messagebox.showerror("File Not Found Error", '{}: `{}`.'.format(e.strerror, e.filename))
        except OSError as e:
            logger.error(e)
            tk.messagebox.showerror("OS Error", e.strerror)
        except DtbReader.InvalidDtbFileError as e:
            logger.error(e)
            tk.messagebox.showerror("Error", e.message)
        else:
            message = 'Conversion finished! CSV file saved to `{}`.'.format(self.output_csv_filepath.get())
            logger.info(message)
            tk.messagebox.showinfo('Success', message)

    @staticmethod
    def about():
        logger.debug('About window shown.')
        tk.messagebox.showinfo('About ' + PROGRAM_NAME,
                               PROGRAM_NAME + ' ' + __version__ + '\n' +
                               PROGRAM_DESCRIPTION + '\n\n' +
                               'Author: ' + __author__ + ', ' + __email__)

    def mainloop(self):
        logger.debug('Main window shown. (mainloop)')
        self.root.mainloop()


def main() -> ExitCode:
    logging.captureWarnings(True)
    warnings.simplefilter('always', ResourceWarning)
    logging.basicConfig(filename='debug.log', filemode='w', level=logging.DEBUG)

    # # NOTE: Console window is hidden via PYW file extension, argument parsing is not used for now.
    # parser = argparse.ArgumentParser(
    #     prog=PROGRAM_NAME,
    #     description=PROGRAM_DESCRIPTION,
    #     epilog=__author__ + ', ' + __email__ + ', 2019.'
    # )
    # parser.add_argument('-v', '--version', action='version', version='%(prog)s {}'.format(__version__))
    # parser.parse_args()

    app = Application()
    app.mainloop()

    return ExitCode.EX_OK


if __name__ == '__main__':
    try:
        exit_code = main()
    except KeyboardInterrupt:
        logger.warning('received KeyboardInterrupt, stopping')
        sys.exit(ExitCode.KEYBOARD_INTERRUPT.value)
    else:
        sys.exit(exit_code.value)
