import plistlib
from pathlib import Path
from uuid import uuid4

WORK = Path(__file__).parent
TRAIN_TYPE = (
    r'(?i:KTX(?:[\p{Zs}\t]*[-–·][\p{Zs}\t]*|[\p{Zs}\t]+)'
    r'(?:산천|이음|청룡)|KTX|ITX(?:[\p{Zs}\t]*[-–·][\p{Zs}\t]*|[\p{Zs}\t]+)'
    r'(?:새마을|청춘|마음)|SRT|무궁화호|새마을호|누리로)'
)
TRAIN_PREFIX = (
    rf'(?i:^[\p{{Zs}}\t]*(?:{TRAIN_TYPE})(?:[\p{{Zs}}\t]*[0-9]+'
    r'[\p{Zs}\t]*(?:호)?(?=[\p{Zs}\t:·]))?[\p{Zs}\t:·]+)'
)
PATTERN = (
    r'(?m)^[\p{Zs}\t]*([0-9]{4})[\p{Zs}\t]*년[\p{Zs}\t]*'
    r'(0?[1-9]|1[0-2])[\p{Zs}\t]*월[\p{Zs}\t]*'
    r'(0?[1-9]|[12][0-9]|3[01])[\p{Zs}\t]*일[^\r\n]*\R'
    r'(?:[^\r\n]*\R){0,5}?'
    r'[\p{Zs}\t]*([^()\r\n]+?)[\p{Zs}\t]*\([\p{Zs}\t]*'
    r'([01]?[0-9]:[0-5][0-9]|2[0-3]:[0-5][0-9])[\p{Zs}\t]*\)'
    r'[\p{Zs}\t]*출발[\p{Zs}\t]*(?:->|→|➝|⇒)[\p{Zs}\t]*'
    r'([^()\r\n]+?)[\p{Zs}\t]*\([\p{Zs}\t]*'
    r'([01]?[0-9]:[0-5][0-9]|2[0-3]:[0-5][0-9])[\p{Zs}\t]*\)'
    r'[\p{Zs}\t]*도착'
)
SHORTCUT_INPUT = {'Type': 'ExtensionInput'}
PAD_PATTERN = r'(?<=[-T])([0-9])(?=[-T:])'


def uuid():
    return str(uuid4()).upper()


def serialized(kind, value):
    return {'WFSerializationType': kind, 'Value': value}


def variable(reference):
    return serialized('WFTextTokenAttachment', reference)


def token(*parts):
    string = ''
    ranges = {}
    for part in parts:
        if isinstance(part, str):
            string += part
        else:
            offset = len(string.encode('utf-16-le')) // 2
            ranges[f'{{{offset}, 1}}'] = part
            string += '\ufffc'
    return serialized('WFTextTokenString', {'string': string, 'attachmentsByRange': ranges})


def build(preview):
    actions = []

    def add(identifier, **parameters):
        actions.append({
            'WFWorkflowActionIdentifier': f'is.workflow.actions.{identifier}',
            'WFWorkflowActionParameters': parameters,
        })

    def output(identifier, name, **parameters):
        uid = uuid()
        add(identifier, UUID=uid, CustomOutputName=name, **parameters)
        return {'Type': 'ActionOutput', 'OutputUUID': uid, 'OutputName': name}

    def match(text):
        return output('text.match', '코레일 승차권', text=token(text),
                      WFMatchTextPattern=PATTERN, WFMatchTextCaseSensitive=True)

    def group(matches, index, name):
        return output('text.match.getgroup', name, matches=variable(matches),
                      WFGetGroupType='Group At Index', WFGroupIndex=index)

    def begin_if(reference, condition, **parameters):
        identifier = uuid()
        add('conditional', GroupingIdentifier=identifier, WFControlFlowMode=0,
            WFInput={'Type': 'Variable', 'Variable': variable(reference)},
            WFCondition=condition, **parameters)
        return identifier

    def end_if(identifier):
        add('conditional', GroupingIdentifier=identifier, WFControlFlowMode=2)

    def guard(reference, message):
        identifier = begin_if(reference, 101)
        if preview:
            add('output', WFOutput=message)
        else:
            add('alert', WFAlertActionTitle='코레일 일정 등록', WFAlertActionMessage=message,
                WFAlertActionCancelButtonShown=False)
        add('exit')
        end_if(identifier)

    def date(hour, name):
        iso = output('text.replace', f'{name} ISO',
                     WFInput=token(year, '-', month, '-', day, 'T', hour, ':00+09:00'),
                     WFReplaceTextFind=PAD_PATTERN, WFReplaceTextReplace='0$1',
                     WFReplaceTextRegularExpression=True)
        dates = output('detect.date', f'{name} 후보', WFInput=variable(iso))
        return output('getitemfromlist', name, WFInput=variable(dates), WFItemSpecifier='First Item')

    matches = match(SHORTCUT_INPUT)
    guard(matches, '코레일톡에서 날짜와 출발·도착 시각이 들어 있는 승차권 문구를 공유해 주세요.')
    first = output('getitemfromlist', '첫 번째 승차권', WFInput=variable(matches), WFItemSpecifier='First Item')
    year, month, day, departure, departure_time, arrival, arrival_time = [
        group(first, index, name)
        for index, name in enumerate(
            ('연도', '월', '일', '출발역', '출발 시각', '도착역', '도착 시각'), 1
        )
    ]
    start = date(departure_time, '출발 날짜')
    finish = date(arrival_time, '도착 날짜')
    guard(start, '출발 날짜와 시각을 읽지 못했습니다.')
    guard(finish, '도착 날짜와 시각을 읽지 못했습니다.')

    add('setvariable', WFVariableName='종료', WFInput=variable(finish))
    midnight = begin_if(
        {**finish, 'Aggrandizements': [
            {'Type': 'WFCoercionVariableAggrandizement', 'CoercionItemClass': 'WFDateContentItem'}
        ]},
        0, WFDate=variable(start),
    )
    next_day = output(
        'adjustdate', '다음 날 도착', WFDate=token(finish), WFAdjustOperation='Add',
        WFDuration=serialized('WFQuantityFieldValue', {'Magnitude': 1, 'Unit': 'days'}),
    )
    add('setvariable', WFVariableName='종료', WFInput=variable(next_day))
    end_if(midnight)

    station = output('text.replace', '출발역 이름', WFInput=token(departure),
                     WFReplaceTextFind=TRAIN_PREFIX, WFReplaceTextReplace='',
                     WFReplaceTextRegularExpression=True)
    boarding_time = output('text.replace', '탑승 시각', WFInput=token(departure_time),
                           WFReplaceTextFind=r'^([0-9]):', WFReplaceTextReplace='0$1:',
                           WFReplaceTextRegularExpression=True)
    title = output('gettext', '일정 제목',
                   WFTextActionText=token(station, ' → ', arrival, ' (', boarding_time, ')'))
    end = {'Type': 'Variable', 'VariableName': '종료'}
    if preview:
        formatted = [
            output('format.date', name, WFDate=token(reference), WFDateFormatStyle='Custom',
                   WFDateFormat='yyyy-MM-dd HH:mm XXX')
            for name, reference in [('시작 확인', start), ('종료 확인', end)]
        ]
        add('output', WFOutput=token(title, '\n', formatted[0], '\n', formatted[1]))
    else:
        add('addnewevent', WFCalendarItemTitle=token(title),
            WFCalendarItemStartDate=token(start), WFCalendarItemEndDate=token(end),
            WFCalendarItemAllDay=False, WFAlertTime='None', ShowWhenRun=False)
        add('nothing')

    return {
        'WFWorkflowClientVersion': '5114.0.6.204',
        'WFWorkflowMinimumClientVersion': 900,
        'WFWorkflowMinimumClientVersionString': '900',
        'WFWorkflowIcon': {'WFWorkflowIconStartColor': 463140863, 'WFWorkflowIconGlyphNumber': 61440},
        'WFWorkflowTypes': [] if preview else ['ActionExtension'],
        'WFQuickActionSurfaces': [],
        'WFWorkflowInputContentItemClasses': ['WFStringContentItem', 'WFRichTextContentItem'],
        'WFWorkflowOutputContentItemClasses': [],
        'WFWorkflowHasShortcutInputVariables': True,
        'WFWorkflowHasOutputFallback': False,
        'WFWorkflowImportQuestions': [],
        'WFWorkflowNoInputBehavior': {
            'Name': 'WFWorkflowNoInputBehaviorAskForInput',
            'Parameters': {'ItemClass': 'WFStringContentItem'},
        },
        'WFWorkflowActions': actions,
    }


for filename, preview in (('Korail Calendar.shortcut', False), ('Korail Calendar Check.shortcut', True)):
    (WORK / filename).write_bytes(plistlib.dumps(build(preview), fmt=plistlib.FMT_BINARY))
