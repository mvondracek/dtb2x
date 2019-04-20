#! /usr/bin/env python
"""
dtb2x
Simple and easy to use DTB to XLSX (and CSV) format converter.
Martin Vondracek <vondracek.mar@gmail.com>
2019
"""

import logging
import os
import sys
import tkinter as tk
import warnings
from enum import Enum, unique
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import showerror

import dtb2x
from dtb2x.core import ConverterCsv, ConverterXlsx, DtbReader

PROGRAM_NAME = 'dtb2x'
PROGRAM_DESCRIPTION = 'Simple and easy to use DTB to XLSX (and CSV) format converter.'
PACKAGE_VERSION = dtb2x.__version__
__author__ = 'Martin Vondracek'
__email__ = 'vondracek.mar@gmail.com'
__version__ = '0.3.0'
__date__ = '2019-04-21'

logger = logging.getLogger(__name__)


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


class Application:
    def __init__(self):
        self.root = tk.Tk()

        self.input_dtb_filepath = tk.StringVar()
        self.output_csv_filepath = tk.StringVar()
        self.dtb_strict_mode = tk.BooleanVar()
        self.dtb_strict_mode.set(True)

        self.root.title(PROGRAM_NAME)
        self.root.resizable(False, False)

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
        self.root.config(menu=menu, pady=5, padx=5)

        tk.Label(self.root, text="Input DTB file:").grid(row=0, column=0)
        tk.Entry(self.root, textvariable=self.input_dtb_filepath, width=40).grid(row=0, column=1)
        tk.Button(self.root, text='Browse...', command=self.ask_input_dtb_filepath).grid(row=0, column=2)

        tk.Checkbutton(self.root, text="DTB strict mode",
                       variable=self.dtb_strict_mode).grid(row=1, column=0, columnspan=3)

        tk.Button(self.root, text='Convert', command=self.convert).grid(row=2, column=0, columnspan=3)
        self.center_window()

    def center_window(self):
        self.root.update_idletasks()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        x_position = (self.root.winfo_screenwidth() // 2) - (window_width // 2)
        y_position = (self.root.winfo_screenheight() // 2) - (window_height // 2)
        self.root.geometry('{}x{}+{}+{}'.format(window_width, window_height, x_position, y_position))

    def ask_input_dtb_filepath(self):
        input_filepath = tk.filedialog.askopenfilename(
            title='Open DTB file',
            filetypes=(("DTB files", "*.dtb"), ("all files", "*.*"))
        )
        logger.debug('Selected input DTB filepath `{}`'.format(input_filepath))
        self.input_dtb_filepath.set(input_filepath)

    def ask_output_filepath(self):
        input_filepath = self.input_dtb_filepath.get()
        if input_filepath:
            initial_file = os.path.splitext(os.path.basename(input_filepath))[0]
            initial_directory = os.path.dirname(input_filepath)
        else:
            initial_file = ''
            initial_directory = ''

        output_filepath = tk.filedialog.asksaveasfilename(
            title='Save file',
            filetypes=(("XLSX files", "*.xlsx"), ("CSV files", "*.csv"), ("all files", "*.*")),
            defaultextension='.xlsx',
            initialfile=initial_file,
            initialdir=initial_directory
        )
        logger.debug('Selected output filepath `{}`'.format(output_filepath))
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
        self.ask_output_filepath()
        output_filepath = self.output_csv_filepath.get()
        if not output_filepath:
            return  # user canceled `asksaveasfilename` dialog

        if output_filepath[-4:] == '.csv':
            converter = ConverterCsv
        elif output_filepath[-5:] == '.xlsx':
            converter = ConverterXlsx
        else:
            warning_message = 'Unsupported output file format `{}`.'.format(output_filepath)
            logger.warning(warning_message)
            tk.messagebox.showwarning("OK", warning_message)
            return
        try:
            with open(input_filepath, mode='r') as dtb_file, \
                    open(output_filepath, mode='w', newline=converter.newline()) as output_file:
                # NOTE: CSV file is opened with `newline=''` to prevent line ends in form `\r\r\n`
                # see https://docs.python.org/3.5/library/csv.html#id3
                strict = self.dtb_strict_mode.get()
                logger.info('Conversion started. input DTB = `{}`, output = `{}`, strict = {}'
                            .format(input_filepath, output_filepath, strict))
                converter.convert(dtb_file, output_file, strict=strict)

        except FileNotFoundError as e:
            logger.error(e)
            tk.messagebox.showerror("File Not Found Error", '{}: `{}`.'.format(e.strerror, e.filename))
        except OSError as e:
            logger.error(e)
            tk.messagebox.showerror("OS Error", e.strerror)
        except UnicodeError as e:
            message = 'Cannot read file.\n\n{}: {}'.format(e.__class__.__name__, str(e))
            logger.error(message)
            tk.messagebox.showerror("Unicode Error", message)
        except DtbReader.InvalidDtbFileError as e:
            logger.error(e)
            message = e.message
            if self.dtb_strict_mode:
                message += '\n\nTry again without DTB strict mode.'
            tk.messagebox.showerror("Error", message)
        else:
            message = 'Conversion finished! File saved to `{}`.'.format(self.output_csv_filepath.get())
            logger.info(message)
            tk.messagebox.showinfo('Success', message)

    @staticmethod
    def about():
        logger.debug('About window shown.')
        tk.messagebox.showinfo('About ' + PROGRAM_NAME,
                               PROGRAM_NAME + '\n' +
                               PROGRAM_DESCRIPTION + '\n\n' +
                               'GUI v' + __version__ + ', package v' + PACKAGE_VERSION + '\n\n' +
                               'Author: ' + __author__ + ', ' + __email__ + '\n' +
                               __date__)

    def mainloop(self):
        logger.debug('Main window shown. (mainloop)')
        self.root.mainloop()


def main() -> ExitCode:
    logging.captureWarnings(True)
    warnings.simplefilter('always', ResourceWarning)
    logging.basicConfig(filename='debug.log', filemode='w', level=logging.DEBUG)

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
