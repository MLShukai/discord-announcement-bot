"""Message templates for Discord announcements.

This module provides templates for different types of announcement
messages that can be sent by the Discord announcement bot.
"""

import datetime
from string import Template


class AnnouncementTemplates:
    """Container for announcement message templates.

    Provides methods to format announcement messages for different event
    types.
    """

    # Template for regular meetings
    REGULAR_TEMPLATE = Template(
        "今週の$mm/$ddのML集会も21時半より開催致します。今週はまったり雑談会です\n$url"
    )

    # Template for lightning talk meetings
    LT_TEMPLATE = Template(
        "今週のML集会はLT会! $mm/$ddの21時半より開催致します。\n"
        "$speaker_nameさんより「$title」を行いますので、ぜひみなさんお越しください！\n"
        "$url"
    )

    # Template for canceled meetings
    REST_TEMPLATE = "今週のML集会はおやすみです。"

    @classmethod
    def format_regular(cls, date: datetime.date, url: str) -> str:
        """Format a regular meeting announcement message.

        Args:
            date: The date of the meeting.
            url: The URL to include in the announcement.

        Returns:
            Formatted announcement message for a regular meeting.
        """
        return cls.REGULAR_TEMPLATE.substitute(mm=date.month, dd=date.day, url=url)

    @classmethod
    def format_lightning_talk(
        cls, date: datetime.date, speaker_name: str, title: str, url: str
    ) -> str:
        """Format a lightning talk meeting announcement message.

        Args:
            date: The date of the meeting.
            speaker_name: The name of the speaker.
            title: The title of the talk.
            url: The URL to include in the announcement.

        Returns:
            Formatted announcement message for a lightning talk meeting.
        """
        return cls.LT_TEMPLATE.substitute(
            mm=date.month, dd=date.day, speaker_name=speaker_name, title=title, url=url
        )

    @classmethod
    def format_rest(cls) -> str:
        """Format a canceled meeting announcement message.

        Returns:
            Formatted announcement message for a canceled meeting.
        """
        return cls.REST_TEMPLATE
