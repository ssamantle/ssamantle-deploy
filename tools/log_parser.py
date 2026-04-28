import dataclasses
import datetime
import pathlib
import re

import pandas as pd


BASE_DIR = pathlib.Path(__file__).parents[1].resolve()

LOG_BASE_PATTERN = re.compile(
    r"(?P<level>\w+):\s+\[(?P<timestamp>.*?)\] \[(?P<sessionId>.*?)\] \[(?P<name>.*?)\] (?P<message>.*)")
# LOG_MESSAGE_SUCCESS_PATTERN = re.compile(r"username=(?P<username>.*?), word=(?P<word>.*?), similarity=(?P<similarity>.*?), wordRank=(?P<wordRank>.*?), gameRank=(?P<gameRank>.*)")
# LOG_MESSAGE_FAIL_PATTERN = re.compile(r"사전에 없는 단어: '(?P<word>.*?)' \(username=(?P<username>.*?)\)")


def parse_log(log_file: pathlib.Path) -> pd.DataFrame:
    data = list(_parse_log_data(log_file))

    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['sessionId'] = df['sessionId'].replace('anonymous', None)

    return df


def _parse_log_data(log_file: pathlib.Path):
    with log_file.open('rt', encoding='UTF-8') as f:
        for line in f.readlines():
            data = _parse_log_row_data(line)
            if data is None:
                continue
            yield data


def _parse_log_row_data(row: str):
    match = LOG_BASE_PATTERN.search(row)
    if not match:
        return None

    return match.groupdict()


def _extract_participant(log_df: pd.DataFrame) -> pd.DataFrame:
    df = log_df[log_df['message'].str.startswith('게임 참가 - ')]

    # "게임 참가 - nickname=김싸피, participantId=124" 형식의 메시지 파싱
    pattern = r"게임 참가 - nickname=(?P<nickname>.*), participantId=(?P<id>\d+)"
    data = df['message'].str.extract(pattern)

    return df.merge(data, left_index=True, right_index=True, suffixes=('', '_log'))


def _extract_game(log_df: pd.DataFrame) -> pd.DataFrame:
    df_game_created = log_df[log_df['message'].str.startswith('게임 생성 - ')]
    df_game_recreated = log_df[log_df['message'].str.startswith(
        '게임 재생성 (덮어쓰기) - ')]

    if not df_game_created.empty:
        # "게임 생성 - host=string, targetWord=사자, status=INGAME" 형식의 메시지 파싱
        pattern = r"게임 생성 - host=(?P<hostname>.+), targetWord=(?P<target_word>.+), status=(?P<status>.+)"
        data = df_game_created['message'].str.extract(pattern)
        return df_game_created.merge(data, left_index=True, right_index=True, suffixes=('', '_log'))

    elif not df_game_recreated.empty:
        # "게임 재생성 (덮어쓰기) - host=string, targetWord=봄바람, status=PREGAME" 형식의 메시지 파싱
        pattern = r"게임 재생성 \(덮어쓰기\) - host=(?P<hostname>.+), targetWord=(?P<target_word>.+), status=(?P<status>.+)"
        data = df_game_recreated['message'].str.extract(pattern)
        return df_game_recreated.merge(data, left_index=True, right_index=True, suffixes=('', '_log'))

    else:
        raise ValueError("게임 생성 또는 재생성 로그가 없습니다.")


def _extract_guess_history(log_df: pd.DataFrame) -> pd.DataFrame:
    df = log_df[log_df['message'].str.startswith('추측 결과 - ')]

    # "추측 결과 - username=7반__고대영, word=공부, similarity=0.0639, wordRank=23207, gameRank=1" 형식의 메시지 파싱
    pattern = r"추측 결과 - username=(?P<nickname>.*), word=(?P<word>.*), similarity=(?P<similarity>.*), wordRank=(?P<word_rank>\d+), gameRank=(?P<game_rank>\d+)"
    data = df['message'].str.extract(pattern)

    return df.merge(data, left_index=True, right_index=True, suffixes=('', '_log'))


def _best_guess_history(log_df: pd.DataFrame) -> pd.DataFrame:
    guess_history_df = _extract_guess_history(log_df)

    best_similarities = guess_history_df.groupby('nickname')[
        'similarity'].max()

    best_guesses = guess_history_df.merge(
        best_similarities, on=['nickname', 'similarity'], suffixes=('', '_best'))
    best_guesses = best_guesses.sort_values(
        'timestamp').drop_duplicates('nickname', keep='first')

    return best_guesses


def _participant_session(log_df: pd.DataFrame) -> pd.DataFrame:
    df = _extract_guess_history(log_df)
    df.drop_duplicates(subset=['nickname', 'sessionId'], inplace=True)
    return df[['nickname', 'sessionId']]


def extract_game(log_df: pd.DataFrame) -> pd.DataFrame:
    df = _extract_game(log_df)

    target_columns = ['hostname', 'host_session_id', 'target_word',
                      'status', 'started_at', 'ended_at', 'created_at']

    df['host_session_id'] = df['sessionId']
    df['started_at'] = None
    df['ended_at'] = None
    df['created_at'] = df['timestamp']

    df.sort_values(by='created_at', inplace=True)

    return df[target_columns].reset_index(drop=True)


def extract_participant(log_df: pd.DataFrame) -> pd.DataFrame:
    df = _extract_participant(log_df)

    game_df = _extract_game(log_df)
    best_guess_df = _best_guess_history(log_df)
    session_df = _participant_session(log_df)

    target_columns = ['id', 'game_id', 'nickname', 'session_id',
                      'best_similarity', 'closest_word', 'is_correct', 'joined_at']

    df['game_id'] = 1
    df['session_id'] = df['nickname'].map(
        session_df.set_index('nickname')['sessionId'])
    df['best_similarity'] = df['nickname'].map(
        best_guess_df.set_index('nickname')['similarity'])
    df['closest_word'] = df['nickname'].map(
        best_guess_df.set_index('nickname')['word'])
    df['is_correct'] = df['closest_word'] == game_df.iloc[0]['target_word']
    df['joined_at'] = df['timestamp']

    df.sort_values(by='joined_at', inplace=True)

    return df[target_columns].reset_index(drop=True)


def extract_guess_history(log_df: pd.DataFrame) -> pd.DataFrame:
    df = _extract_guess_history(log_df)

    game_df = _extract_game(log_df)
    participant_df = _extract_participant(log_df)

    target_columns = ['participant_id', 'nickname', 'word',
                      'similarity', 'word_rank', 'is_answer', 'submitted_at']

    df['participant_id'] = df['nickname'].map(
        participant_df.set_index('nickname')['id'])
    df['is_answer'] = df['word'] == game_df.iloc[0]['target_word']
    df['submitted_at'] = df['timestamp']

    df.sort_values(by='submitted_at', inplace=True)

    return df[target_columns].reset_index(drop=True)


@dataclasses.dataclass
class GameData:
    game: pd.DataFrame
    participant: pd.DataFrame
    guess_history: pd.DataFrame


def parse_game_log(log_file: pathlib.Path, start_time: datetime.datetime, end_time: datetime.datetime) -> GameData:
    log_df = parse_log(log_file)

    # Filter logs by time range
    log_df = log_df[(log_df['timestamp'] >= start_time)
                    & (log_df['timestamp'] <= end_time)]

    game_df = extract_game(log_df)
    participant_df = extract_participant(log_df)
    guess_history_df = extract_guess_history(log_df)

    game_df['started_at'] = start_time
    game_df['ended_at'] = end_time

    return GameData(
        game=game_df,
        participant=participant_df,
        guess_history=guess_history_df
    )


if __name__ == '__main__':
    df = parse_log(BASE_DIR / 'volume/server/logs/app.log')
    df.to_csv(BASE_DIR / 'app.log.csv', index=False)
