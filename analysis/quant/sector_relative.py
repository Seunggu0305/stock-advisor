"""섹터 상대 강도 분석"""

from models.schemas import SectorRelativeResult


def analyze_sector_relative(stock_info: dict | None, sector_etfs: dict | None) -> SectorRelativeResult:
    if stock_info is None or sector_etfs is None:
        return SectorRelativeResult()

    sector = stock_info.get("sector", "Unknown")
    if not sector_etfs:
        return SectorRelativeResult(sector_name=sector)

    # 섹터별 수익률 순위
    sorted_sectors = sorted(sector_etfs.items(), key=lambda x: x[1].get("return_1m", 0), reverse=True)
    total = len(sorted_sectors)

    # 현재 종목 섹터 찾기
    rank = 0
    rel_strength = 0.0
    for i, (sec_name, data) in enumerate(sorted_sectors):
        if sector.lower() in sec_name.lower() or sec_name.lower() in sector.lower():
            rank = i + 1
            rel_strength = data.get("return_1m", 0)
            break

    if rank == 0:
        # 정확한 매칭이 안 되면 기본값
        rank = total // 2
        rel_strength = 0

    # 점수: 상위 섹터일수록 높은 점수
    if total > 0:
        score = (1 - (rank - 1) / total) * 100
    else:
        score = 50

    return SectorRelativeResult(
        sector_name=sector,
        relative_strength=round(rel_strength, 2),
        sector_rank=rank,
        total_sectors=total,
        score=round(score, 1),
    )
