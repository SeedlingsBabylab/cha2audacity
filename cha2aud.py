import sys
import re
import datetime

class Block:
    def __init__(self, index):

        self.index = index
        self.num_clips = None
        self.clips = []
        self.sliced = False
        #self.contains_fan_or_man = False
        self.dont_share = False
        self.id = ""
        self.coder = None
        self.lab_key = None
        self.lab_name = None
        self.old = False

    def sort_clips(self):
        self.clips.sort(key=lambda x: x.clip_index)

class Clip:
    def __init__(self, block_index, clip_index):
        self.parent_audio_path = None
        self.clan_file = None
        self.block_index = block_index
        self.clip_index = clip_index
        self.clip_tier = None
        self.multiline = False
        self.multi_tier_parent = None
        self.start_time = None
        self.offset_time = None
        self.end_time = None
        self.timestamp = None
        self.classification = None
        self.gender_label = None
        self.label_date = None
        self.coder = None
        self.lab_key = None




the_block = None


interval_regx = re.compile("\\x15\d+_\d+\\x15")


def parse_clan(path):
    global the_block
    conversation = []

    curr_conversation = []
    with open(path, "rU") as file:
        for line in file:
            if line.startswith("@Bg:\tConversation {}".format(block_num)):
                conversation.append(line)
                continue
            if conversation:
                conversation.append(line)
            if line.startswith("@Eg:\tConversation {}".format(block_num)):
                break
                # conversation.append(curr_conversation)
                # curr_conversation = []

    conversation_block = filter_conversation(conversation)

    the_block = create_clips(conversation_block, block_num)

    # for index, block in enumerate(conversation_block):
    #     self.clip_blocks.append(self.create_clips(block, path, index + 1))

    find_multitier_parents()

def filter_conversation(conversation):

    last_tier = ""

    conv_block = []
    for line in conversation:
        if line.startswith("%"):
            continue
        elif line.startswith("@"):
            continue
        elif line.startswith("*"):
            last_tier = line[0:4]
            conv_block.append(line)
        else:
            conv_block.append(last_tier + line + "   MULTILINE")

    return conv_block


def find_multitier_parents():
    for clip in the_block.clips:
        if clip.multiline:
            reverse_parent_lookup(the_block, clip)


def reverse_parent_lookup(block, multi_clip):
    for clip in reversed(block.clips[0:multi_clip.clip_index - 1]):
        if clip.multiline:
            continue
        else:
            multi_clip.multi_tier_parent = clip.timestamp
            return


def create_clips(clips, block_index):

    block = Block(block_index)
    first_clip_onset = None

    for index, clip in enumerate(clips):

        curr_clip = Clip(block_index, index + 1)
        curr_clip.clip_tier = clip[1:4]
        if "MULTILINE" in clip:
            curr_clip.multiline = True

        interval_reg_result = interval_regx.search(clip)
        if interval_reg_result:
            interval_str = interval_reg_result.group().replace("\x15", "")
            curr_clip.timestamp = interval_str

        time = interval_str.split("_")
        time = [int(time[0]), int(time[1])]

        if index == 0:
            first_clip_onset = time[0]
            print time

        time = [x-first_clip_onset for x in time]

        final_time = ms_to_s(time)

        curr_clip.start_time = final_time[0]
        curr_clip.end_time = final_time[1]
        # curr_clip.offset_time = str(final_time[2])

        block.clips.append(curr_clip)

    block.num_clips = len(block.clips)

    for clip in block.clips:
        if clip.clip_tier == "FAN":
            block.contains_fan_or_man = True
        if clip.clip_tier == "MAN":
            block.contains_fan_or_man = True

    return block


def ms_to_s(interval):
    seconds = [float(x)/1000 for x in interval]
    return seconds


def to_audacity_labels(block):


    with open(output, "wb") as out:
        for clip in block.clips:
            out.write("{:.6f} {:.6f} {}\n".format(clip.start_time, clip.end_time, clip.clip_tier))

if __name__ == "__main__":

    block_num = sys.argv[1]
    cha_file = sys.argv[2]
    output = sys.argv[3]

    parse_clan(cha_file)

    to_audacity_labels(the_block)
