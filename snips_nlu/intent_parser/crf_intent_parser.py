from intent_parser import IntentParser
from snips_nlu.intent_classifier.intent_classifier import IntentClassifier
from snips_nlu.result import ParsedSlot
from snips_nlu.slot_filler.crf_tagger import CRFTagger
from snips_nlu.slot_filler.crf_utils import (tags_to_slots,
                                             utterance_to_sample)
from snips_nlu.tokenization import tokenize
from snips_nlu.utils import instance_to_generic_dict


def get_slot_name_to_entity_mapping(dataset):
    slot_name_to_entity = dict()
    for intent in dataset["intents"].values():
        for utterance in intent["utterances"]:
            for chunk in utterance["data"]:
                if "slot_name" in chunk:
                    slot_name_to_entity[chunk["slot_name"]] = chunk["entity"]
    return slot_name_to_entity


class CRFIntentParser(IntentParser):
    def __init__(self, intent_classifier, crf_taggers,
                 slot_name_to_entity_mapping=None):
        super(CRFIntentParser, self).__init__()
        self.intent_classifier = intent_classifier
        self.crf_taggers = crf_taggers
        self.slot_name_to_entity_mapping = slot_name_to_entity_mapping

    def get_intent(self, text):
        if not self.fitted:
            raise ValueError("CRFIntentParser must be fitted before "
                             "`get_intent` is called")
        return self.intent_classifier.get_intent(text)

    def get_slots(self, text, intent=None):
        if intent is None:
            raise ValueError("intent can't be None")
        if not self.fitted:
            raise ValueError("CRFIntentParser must be fitted before "
                             "`get_slots` is called")
        if intent not in self.crf_taggers:
            raise KeyError("Invalid intent '%s'" % intent)
        tokens = tokenize(text)
        tagger = self.crf_taggers[intent]

        tags = tagger.get_tags(tokens)
        slots = tags_to_slots(tokens, tags, tagging=tagger.tagging)
        return [ParsedSlot(match_range=s["range"],
                           value=text[s["range"][0]:s["range"][1]],
                           entity=self.slot_name_to_entity_mapping[
                               s["slot_name"]],
                           slot_name=s["slot_name"]) for s in slots]

    @property
    def fitted(self):
        return self.intent_classifier.fitted and all(
            slot_filler.fitted for slot_filler in self.crf_taggers.values())

    def fit(self, dataset):
        self.slot_name_to_entity_mapping = get_slot_name_to_entity_mapping(
            dataset)
        self.intent_classifier = self.intent_classifier.fit(dataset)

        for intent_name in dataset["intents"]:
            intent_utterances = dataset["intents"][intent_name]["utterances"]
            tagging = self.crf_taggers[intent_name].tagging
            crf_samples = [utterance_to_sample(u["data"], tagging)
                           for u in intent_utterances]
            self.crf_taggers[intent_name] = self.crf_taggers[intent_name].fit(
                crf_samples)
        return self

    def to_dict(self):
        obj_dict = instance_to_generic_dict(self)
        obj_dict.update({
            "intent_classifier": self.intent_classifier.to_dict(),
            "crf_taggers": {intent_name: tagger.to_dict() for
                            intent_name, tagger in
                            self.crf_taggers.iteritems()},
            "slot_name_to_entity_mapping": self.slot_name_to_entity_mapping
        })
        return obj_dict

    @classmethod
    def from_dict(cls, obj_dict):
        return CRFIntentParser(
            intent_classifier=IntentClassifier.from_dict(
                obj_dict["intent_classifier"]),
            crf_taggers={intent_name: CRFTagger.from_dict(tagger_dict)
                         for intent_name, tagger_dict in
                         obj_dict["crf_taggers"].iteritems()},
            slot_name_to_entity_mapping=obj_dict["slot_name_to_entity_mapping"]
        )