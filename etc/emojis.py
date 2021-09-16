from enum import Enum

class Emojis(Enum):
    BASE_GRADE = "<:basegrade:874985683029225542>"
    INDUSTRIAL_GRADE = "<:industrialgrade:874985682525884417>"
    CONSUMER_GRADE = "<:consumergrade:874985682932756480>"
    MILSPEC_GRADE = "<:milspec:874985682790133771>"
    RESTRICTED = "<:restricted:874985683175997461>"
    CLASSIFIED = "<:classified:874985683066949672>"
    COVERT = "<:covert:874985682970488872>"
    CONTRABAND = "<:contraband:874985682924339270>"

    SUPPORTER = "<:supporter:888033002700034078>"


emojis = {
    "Base Grade": Emojis.BASE_GRADE.value,
    "Industrial Grade": Emojis.INDUSTRIAL_GRADE.value,
    "Consumer Grade": Emojis.CONSUMER_GRADE.value,
    "Mil-Spec Grade": Emojis.MILSPEC_GRADE.value,
    "Restricted": Emojis.RESTRICTED.value,
    "Classified": Emojis.CLASSIFIED.value,
    "Covert": Emojis.COVERT.value,
    "Extraordinary": Emojis.COVERT.value,
    "Exceedingly Rare Item": Emojis.COVERT.value,
    "Contraband": Emojis.CONTRABAND.value,
    "Supporter": Emojis.SUPPORTER.value
}