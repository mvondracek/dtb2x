# dtb2x
Simple and easy to use DTB to XLSX (and CSV) format converter.

[![Python version](https://img.shields.io/badge/Python-3-blue.svg?style=flat-square)](https://www.python.org/)

![dtb2xgui](doc/dtb2xgui.png)

*The graphical user interface of the dtb2xgui converter.*

# Installation

On Windows, **double click** `install.bat` or install requirements from `requirements.txt` using `pip`.

# Run

**Double click** `dtb2xgui.pyw` or you can also run `python dtb2xgui.pyw` from the command line.

The application saves logs to the `debug.log` file.

## Conversion process

Input DTB format defines a hierarchy of sports groups, teams, and players. Each team is indented with a single tab `\t`,
and each player is indented with two tabs `\t\t`.

A group contains teams, it is a top-level record in DTB file. A team belongs to a single group and contains players.
Each player belongs to a single team. Please see `dtb2x.core.DtbReader` for a specification of individual fields.

Example files are in `example` directory.

### DTB input

~~~
group_name - group_note
	team_name - team_note
		00001234 - player_surname player_name, 01.01.1900 , player_note
~~~
*Listing: Example input DTB file.*

### XLSX output

*Table: Corresponding XLSX table, including table header in Czech.*

| Název, Oddíl | Poznámka, Oddíl | Název, Družstvo | Poznámka, Družstvo | Reg. číslo, Hráč | Jméno, Hráč | Příjmení, Hráč | Datum nar., Hráč | Poznámka, Hráč |
|--------------|-----------------|-----------------|--------------------|------------------|-------------|----------------|------------------|----------------|
|group_name|group_note|							
|group_name|group_note|team_name|team_note|					
|group_name|group_note|team_name|team_note|00001234|player_name|player_surname|01.01.1900|player_note|

### CSV output

Microsoft Excel expects delimiter in CSV files based on regional settings, `;` is used here. We also use usual
properties of an Excel-generated CSV file as defined in
[csv.excel](https://docs.python.org/3.7/library/csv.html#csv.excel).

~~~
Název, Oddíl;Poznámka, Oddíl;Název, Družstvo;Poznámka, Družstvo;Reg. číslo, Hráč;Jméno, Hráč;Příjmení, Hráč;Datum nar., Hráč;Poznámka, Hráč
group_name;group_note;;;;;;;
group_name;group_note;team_name;team_note;;;;;
group_name;group_note;team_name;team_note;00001234;player_name;player_surname;01.01.1900;player_note
~~~
*Listing: Corresponding CSV file, including table header in Czech.*

## Strict mode
Convert DTB files to CSV using strict mode for reading DTB file and validation of its format. When strict mode is
enabled, trying to convert DTB file containing format mistakes raises exceptions. If strict mode is disabled,
the reader tries to tolerate small formatting mistakes like missing spaces and missing commas.

## Useful links
- https://www.python-course.eu/python_tkinter.php
- http://effbot.org/tkinterbook/
