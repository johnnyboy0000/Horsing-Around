# -*- coding: utf-8 -*-
# The above line is for turkish characters in comments, unless it is there a encoding error is raised in the server
from enum import Enum


class ManagerType(Enum):
    """
    The class of the columns in the each race table
    """
    Jockey = 'JokeAdi'
    Owner = 'SahipAdi'
    Trainer = 'AntronorAdi'


class ResultRowScrapper:
    def __init__(self, html_row):
        self.row = html_row

    def get(self):
        from scrapper.models import RaceResult
        result = RaceResult()

        # Get the result of the horse from the second column
        result.result = self.get_column_content("SONUCNO")

        # Horses might not run that race or cannot finish it for various reasons. In that case what we get is an
        # empty string, we mark it as -1 if that happens
        if not result.result:
            result.result = -1
        else:
            result.result = int(result.result)

        # The third column in the table contains the name of the horse and a link that goes to that horse's page.
        # Also the link will have the id of the horse and the abbreviations that come after the name which tells
        # status information, for example whether the horse will run with a eye patch and etc.
        # More info is here: http://www.tjk.org/TR/YarisSever/Static/Page/Kisaltmalar
        horse_name_html = self.get_column("AtAdi3").find('a')

        # first element is the name it self, others are the abbreviations, so we get the first and assign it as name
        # after trimming a little. The reason of the trim is to get rid of the number in the parenthesis
        # Example "KARAHİNDİBAYA (7)" -> "KARAHİNDİBAYA"
        result.horse_name = horse_name_html.contents[0].split("(")[0]

        # Now get the id of the horse from that url
        result.horse_id = int(self.get_id_from_a(horse_name_html))

        # Get the result of the horse from the fourth column
        result.horse_age = self.get_column_content("Yas")

        # Horses father and mother are combined in a single column in separate <a> So we find all the <a> in the
        # column and only get their id's from respected links. Father is the first, mother is the second
        parent_links = self.get_column("Baba").find_all('a', href=True)

        # Process the father
        result.horse_father_id = int(self.get_id_from_a(parent_links[0]))

        # Process the mother
        result.horse_mother_id = int(self.get_id_from_a(parent_links[1]))

        # Get the weight of the horse during the time of the race
        result.horse_weight = self.get_column_content("Kilo")

        # Jockey, owner and trainer's have their id's just like the horse's own id. We are only interested in their
        # ids so we don't bother to get their names
        result.jockey_id = self.get_manager_id(ManagerType.Jockey)
        result.owner_id = self.get_manager_id(ManagerType.Owner)
        result.trainer_id = self.get_manager_id(ManagerType.Trainer)

        # Get the time that it took horse to run this race
        result.time = self.get_column_content("Derece")

        # Hc and Hk are two different handicap types that is possible
        result.handicap = int(self.get_column_content("Hc") or self.get_column_content("Hk"))

        return result

    def get_column(self, col_name):
        """
        :param col_name: The value after the gunluk-GunlukYarisSonuclari-{0}
        :return: The content in the column(td) that has a class name starting with gunluk-GunlukYarisSonuclari-
        """
        return self.row.find("td", class_="gunluk-GunlukYarisSonuclari-{0}".format(col_name))

    def get_column_content(self, col_name):
        """
        Striped_strings property returns a collection containing the values. Then ve do a string join to have the
        actual value in the tag. The value might me missing, then we simply return -1 to indicate that it is missing.
        :param col_name: The value after the gunluk-GunlukYarisSonuclari-{0}
        :return: The content in the column(td) that has a class name starting with gunluk-GunlukYarisSonuclari-
        """
        column = self.get_column(col_name)
        return "".join(column.stripped_strings if column else '-1')

    def get_manager_id(self, _type):
        """
        :param _type: The content of the column where the according type of manager is
        :return: id of the desired manager either Jockey, Owner or Trainer
        """
        return int(self.get_id_from_a(self.get_column(_type.value).find('a', href=True)))

    @staticmethod
    def get_id_from_a(a):
        """"
        The url's contain the id, after the phrase Id=
        :param a: The html code of a tag
        :return: id of the supplied a tag
        """
        # We split from that and take the rest
        id_ = a['href'].split("Id=")[1]

        # We split one more time in case of there is more after the id
        # We take the first part this time
        id_ = id_.split("&")[0]

        return id_
