"""저장 CSV의 형식/내부 일관성 검사. 네트워크 접속 및 원본 수정 없음."""
import argparse
import csv
import re
from pathlib import Path

SCHEDULE = ['도시', '극장', '시작시간', '종료시간', '상영타입', '상영관', '잔여좌석', '전체좌석']
MOVIES = ['rank', 'img_src', 'img_title', 'mx4d', 'dolby', 'atmos', 'mega_only',
          'summary', 'score', 'title', 'booking_rate', 'release_date', 'like']
ROOT = Path(__file__).resolve().parents[1]


def valid_time(value, end=False):
    # 극장 영업일 표기: 24~29시 허용. 종료시간의 원본 '~' 접두사 허용.
    pattern = r'~?(?:[01]\d|2\d):[0-5]\d' if end else r'(?:[01]\d|2\d):[0-5]\d'
    return re.fullmatch(pattern, value) is not None


def validate(path, kind):
    errors, warnings = [], []
    expected = SCHEDULE if kind == 'schedule' else MOVIES
    try:
        with Path(path).open(encoding='utf-8-sig', newline='') as stream:
            reader = csv.reader(stream)
            header = next(reader, [])
            indexed = kind == 'schedule' and header == ['', *expected]
            if header != expected and not indexed:
                return 0, [f'열 불일치: {header!r}'], []
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        return 0, [str(exc)], []
    if indexed:
        warnings.append('원본 pandas 인덱스 열을 데이터 중복 검사에서 제외함')
    if not rows:
        errors.append('데이터 행 없음')
    seen = set()
    for number, raw in enumerate(rows, 2):
        if len(raw) != len(header):
            errors.append(f'행 {number}: 열 개수 불일치')
            continue
        values = raw[1:] if indexed else raw
        row = dict(zip(expected, values))
        key = tuple(values)
        if key in seen:
            warnings.append(f'행 {number}: 완전히 동일한 데이터 행')
        seen.add(key)
        required = SCHEDULE if kind == 'schedule' else ['title']
        for name in required:
            if not row[name].strip():
                errors.append(f'행 {number}: {name} 비어 있음')
        if kind == 'schedule':
            for name in ['시작시간', '종료시간']:
                if not valid_time(row[name], end=name == '종료시간'):
                    errors.append(f'행 {number}: {name} 형식 오류')
            seats = [row['잔여좌석'], row['전체좌석']]
            if not all(re.fullmatch(r'[0-9]+', s) for s in seats):
                errors.append(f'행 {number}: 좌석은 음이 아닌 정수여야 함')
            elif not 0 <= int(seats[0]) <= int(seats[1]) or int(seats[1]) == 0:
                errors.append(f'행 {number}: 좌석 수 범위 오류')
        else:
            for name in ['mx4d', 'dolby', 'atmos', 'mega_only']:
                if row[name] not in {'0', '1'}:
                    errors.append(f'행 {number}: {name}은 0/1이어야 함')
    return len(rows), errors, warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--schedule', type=Path, default=ROOT / 'Megabox_Zootopia2_Seoul_1129.csv')
    parser.add_argument('--movies', type=Path, default=ROOT / 'megaboxCrawling.csv')
    args = parser.parse_args()
    failed = False
    for path, kind in [(args.schedule, 'schedule'), (args.movies, 'movies')]:
        count, errors, warnings = validate(path, kind)
        print(f'{path.name}: {count}행, 오류 {len(errors)}, 경고 {len(warnings)}')
        for message in errors + warnings:
            print('  ' + message)
        failed |= bool(errors)
    return int(failed)


if __name__ == '__main__':
    raise SystemExit(main())
