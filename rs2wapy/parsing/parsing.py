import re
import sys
from typing import List
from typing import Sequence

from bs4 import BeautifulSoup
from logbook import Logger
from logbook import StreamHandler

import rs2wapy.models as models

StreamHandler(sys.stdout, level="WARNING").push_application()
logger = Logger(__name__)

TEAMCOLOR_PATTERN = re.compile(r"background: (.*);")


class RS2WebAdminResponseParser:

    def __init__(self, encoding: str):
        self._encoding = encoding

    def parse_html(self, resp: bytes, encoding: str = None) -> BeautifulSoup:
        if not encoding:
            encoding = self._encoding
        return BeautifulSoup(resp.decode(encoding), features="html.parser")

    def parse_chat_messages(self, resp: bytes,
                            encoding: str = None) -> models.ChatMessages:
        parsed_html = self.parse_html(resp, encoding)
        chat_message_divs = parsed_html.find_all(
            "div", attrs={"class": "chatmessage"})
        # parsed_html.find_all("div", attrs={"class": "chatnotice"})
        cm = models.ChatMessages()
        for div in chat_message_divs:
            cm.append(self.parse_chat_message(div))
        return cm

    @staticmethod
    def parse_chat_message(div: BeautifulSoup) -> models.ChatMessage:
        teamcolor = str(div.find(
            "span", attrs={"class": "teamcolor"}).get("style"))
        if not teamcolor:
            logger.error(
                "no teamcolor in chat message div={div}", div=div)
        else:
            try:
                teamcolor = re.match(TEAMCOLOR_PATTERN, teamcolor).groups()[0]
            except IndexError as ie:
                logger.error("error getting teamcolor: {e}", e=ie)

        teamnotice = div.find("span", attrs={"class": "teamnotice"})
        if teamnotice:
            teamnotice = teamnotice.text

        name = div.find("span", attrs={"class": "username"})
        if name:
            name = name.text

        msg = div.find("span", attrs={"class": "message"})
        if msg:
            msg = msg.text

        return models.ChatMessage(
            sender=name,
            text=msg,
            team=models.Team.from_hex_color(str(teamcolor)),
            channel=models.ChatChannel.from_teamnotice(teamnotice)
        )

    def parse_access_policy(self, resp: bytes,
                            encoding: str = None) -> List[str]:
        parsed_html = self.parse_html(resp, encoding)
        policy_table = parsed_html.find("table", attrs={"id": "policies"})
        trs = policy_table.find_all("tr")
        policies = []
        for tr in trs:
            ip_mask = tr.find("input", attrs={"name": "ipmask"})
            policy = tr.find("option", attrs={"selected": "selected"})
            if ip_mask and policy:
                policies.append(
                    f"{ip_mask.get('value')}: {policy.text.upper()}")
        return policies

    def parse_current_game(self, resp: bytes) -> models.CurrentGame:
        parsed_html = self.parse_html(resp)
        ranked = parsed_html.find(
            "span", attrs={"class": "ranked"}).text
        ranked = True if ranked.lower() == "ranked: yes" else False

        player_scoreboard_table = parsed_html.find(
            "table", attrs={"id": "players"})

        player_scoreboard = models.PlayerScoreboard()
        player_scoreboard_thead = player_scoreboard_table.find("thead")
        headers = player_scoreboard_thead.find_all(
            "a", attrs={"class": "sortable"})
        header = ["Team"]
        header.extend([h.text.strip() for h in headers])
        header.extend(["Admin", "Spectator"])
        player_scoreboard.header = header

        row_elements = player_scoreboard_table.find_all("tr")
        scoreboard_parsed = self._parse_table(row_elements)
        for cols in scoreboard_parsed:
            cols[0] = "North" if cols[0] == "0" else "South"
            player_scoreboard.append(cols)

        team_scoreboard_table = parsed_html.find(
            "table", attrs={"id": "teams"})

        team_scoreboard = models.TeamScoreboard()
        team_scoreboard_thead = team_scoreboard_table.find("thead")
        headers = team_scoreboard_thead.find_all("th")
        headers = [h.text.strip() for h in headers if h.text.strip()]
        team_scoreboard.header = headers

        row_elements = team_scoreboard_table.find_all("tr")
        scoreboard_parsed = self._parse_table(row_elements)
        for cols in scoreboard_parsed:
            cols = cols[1:]
            if not len(cols) == len(scoreboard_parsed[0]):
                cols.append("")
            team_scoreboard.append(cols)

        return models.CurrentGame(
            player_scoreboard=player_scoreboard,
            team_scoreboard=team_scoreboard,
            ranked=ranked,
        )

    @staticmethod
    def _parse_table(row_elements: Sequence) -> List[List[str]]:
        all_cols = []
        for row in row_elements:
            cols = row.find_all("td")
            cols = [ele.text.strip() for ele in cols]
            if not cols:
                continue
            cols = [ele for ele in cols if ele]
            all_cols.append(cols)
        return all_cols
