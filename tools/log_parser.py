import pathlib
import re

import pandas as pd


BASE_DIR = pathlib.Path(__file__).parents[1].resolve()

LOG_BASE_PATTERN = re.compile(r"(?P<level>\w+):\s+\[(?P<timestamp>.*?)\] \[(?P<sessionId>.*?)\] \[(?P<name>.*?)\] (?P<message>.*)")
LOG_MESSAGE_SUCCESS_PATTERN = re.compile(r"username=(?P<username>.*?), word=(?P<word>.*?), similarity=(?P<similarity>.*?), wordRank=(?P<wordRank>.*?), gameRank=(?P<gameRank>.*)")
LOG_MESSAGE_FAIL_PATTERN = re.compile(r"사전에 없는 단어: '(?P<word>.*?)' \(username=(?P<username>.*?)\)")


def main():
    log_file = BASE_DIR / 'volume/server/logs/app.log'

    data = list(parse_log(log_file))

    df = pd.DataFrame(data)

    # 숫자형 데이터 타입 변환
    df['similarity'] = pd.to_numeric(df['similarity'])
    df['wordRank'] = pd.to_numeric(df['wordRank'])
    df['gameRank'] = pd.to_numeric(df['gameRank'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    df.to_csv(BASE_DIR / 'log.csv', index=False)


def parse_log(log_file: pathlib.Path):
    with log_file.open('rt', encoding='UTF-8') as f:
        for line in f.readlines():
            data = parse_log_row(line)
            if data is None:
                continue
            yield data


def parse_log_row(row: str):
    match = LOG_BASE_PATTERN.search(row)
    if not match:
        return None
    data = match.groupdict()
    message = data.pop('message')
    parse_log_message(message, data)
    return data


def parse_log_message(message: str, row: dict):
    if "추측 결과" in message:
        # 결과값 상세 파싱
        row.update(LOG_MESSAGE_SUCCESS_PATTERN.search(message).groupdict())
        return
    if "추측 실패" in message:
        # 실패 상세 파싱 (단어와 유저명)
        row.update(LOG_MESSAGE_FAIL_PATTERN.search(message).groupdict())
        return

    print(f"알 수 없는 로그 메시지 형식: \"{message}\"")


if __name__ == '__main__':
    main()
