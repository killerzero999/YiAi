# -*- coding: utf-8 -*-
"""
《五行精纪》气与时间引擎模型
完整版：包含动态动量、旺衰、生克、方位、空亡墓库、大运流年等
"""

import math
from typing import Tuple, List, Optional

# ================== 辅助数据 ==================
# 六十甲子纳音五行表（仅列部分，完整版可扩展）
NAYIN_MAP = {
    '甲子':'金','乙丑':'金','丙寅':'火','丁卯':'火','戊辰':'木','己巳':'木','庚午':'土','辛未':'土','壬申':'金','癸酉':'金',
    '甲戌':'火','乙亥':'火','丙子':'水','丁丑':'水','戊寅':'土','己卯':'土','庚辰':'金','辛巳':'金','壬午':'木','癸未':'木',
    '甲申':'水','乙酉':'水','丙戌':'土','丁亥':'土','戊子':'火','己丑':'火','庚寅':'木','辛卯':'木','壬辰':'水','癸巳':'水',
    '甲午':'金','乙未':'金','丙申':'火','丁酉':'火','戊戌':'木','己亥':'木','庚子':'土','辛丑':'土','壬寅':'金','癸卯':'金',
    '甲辰':'火','乙巳':'火','丙午':'水','丁未':'水','戊申':'土','己酉':'土','庚戌':'金','辛亥':'金','壬子':'木','癸丑':'木',
    '甲寅':'水','乙卯':'水','丙辰':'土','丁巳':'土','戊午':'火','己未':'火','庚申':'木','辛酉':'木','壬戌':'水','癸亥':'水',
}

# 旺相休囚死基准气量
QI_BASE = {'旺': 80, '相': 60, '休': 40, '囚': 30, '死': 20}

# ================== Qi 类（动态动量） ==================
class Qi:
    """气：具有量、纯度、动态动量（向量）、状态"""
    
    # 五行动量方向（单位向量）
    MOMENTUM_VECTORS = {
        '木': (1, 0),    # 散 → 东
        '火': (0, 1),    # 升 → 南
        '土': (0, 0),    # 平 → 中央
        '金': (-1, 0),   # 聚 → 西
        '水': (0, -1),   # 降 → 北
    }
    
    # 五行生成数（生数, 成数）
    GENERATION_NUM = {
        '水': (1, 6),
        '火': (2, 7),
        '木': (3, 8),
        '金': (4, 9),
        '土': (5, 10),
    }
    
    # 地支方位向量
    ZHI_DIRECTION = {
        '寅': (1,0), '卯': (1,0), '辰': (1,0),
        '巳': (0,1), '午': (0,1), '未': (0,1),
        '申': (-1,0), '酉': (-1,0), '戌': (-1,0),
        '亥': (0,-1), '子': (0,-1), '丑': (0,-1),
    }
    
    # 旺衰系数
    PROSPERITY_FACTOR = {'旺': 1.2, '相': 1.0, '休': 0.8, '囚': 0.6, '死': 0.4}
    
    def __init__(self, amount: int = 50, purity: int = 5, wuxing: str = '土', base_zhi: str = '辰'):
        self.amount = amount
        self.purity = purity
        self.wuxing = wuxing
        self.base_zhi = base_zhi
        self._prosperity = '休'          # 旺相休囚死
        self._momentum_vector = self.MOMENTUM_VECTORS[wuxing]
        self._momentum_intensity = 1.0
        self.state = 'active'            # active, hidden(空亡), stored(墓库)
        
        sheng, cheng = self.GENERATION_NUM[wuxing]
        self._base_intensity = cheng / sheng   # 基础强度（生成数比率）
    
    def update_prosperity(self, prosperity: str):
        """更新旺衰，重新计算动量强度"""
        self._prosperity = prosperity
        factor = self.PROSPERITY_FACTOR.get(prosperity, 1.0)
        self._momentum_intensity = self._base_intensity * factor
    
    def apply_direction_modulation(self, zhi: str = None):
        """根据地支方位调制动量强度（方向可能逆转）"""
        if zhi is None:
            zhi = self.base_zhi
        zhi_vec = self.ZHI_DIRECTION.get(zhi, (0,0))
        if zhi_vec == (0,0):
            return
        dot = self._momentum_vector[0]*zhi_vec[0] + self._momentum_vector[1]*zhi_vec[1]
        if dot > 0:
            self._momentum_intensity *= 1.2
        elif dot < 0:
            self._momentum_intensity *= 0.8
            if self._prosperity == '死':
                # 方向逆转
                self._momentum_vector = (-self._momentum_vector[0], -self._momentum_vector[1])
    
    def interact_with_other(self, other: 'Qi', relation: str):
        """
        生克交互：relation = 'generate' 或 'restrict'
        生：self 生 other；克：self 克 other
        """
        if relation == 'generate':
            angle = self._angle_between(self._momentum_vector, other._momentum_vector)
            efficiency = max(0, 1 - angle / 180.0)
            transfer = 5 * efficiency
            if self.amount >= transfer:
                self.amount -= transfer
                other.amount += transfer
                other.purity = (self.purity + other.purity) // 2
        elif relation == 'restrict':
            angle = self._angle_between(self._momentum_vector, other._momentum_vector)
            # 夹角越接近180°，克力越大
            power = max(0, (180 - abs(angle - 180)) / 180.0)
            loss_self = 3 * power
            loss_other = 5 * power
            self.amount = max(0, self.amount - loss_self)
            other.amount = max(0, other.amount - loss_other)
            self.purity = max(0, self.purity - 1)
            other.purity = max(0, other.purity - 1)
    
    @staticmethod
    def _angle_between(v1: Tuple[float,float], v2: Tuple[float,float]) -> float:
        dot = v1[0]*v2[0] + v1[1]*v2[1]
        norm1 = math.hypot(v1[0], v1[1])
        norm2 = math.hypot(v2[0], v2[1])
        if norm1 == 0 or norm2 == 0:
            return 90.0
        cos = dot / (norm1 * norm2)
        cos = max(-1, min(1, cos))
        return math.degrees(math.acos(cos))
    
    # 兼容旧接口
    @property
    def momentum(self) -> str:
        inv = {(1,0):'散', (0,1):'升', (-1,0):'聚', (0,-1):'降', (0,0):'平'}
        return inv.get(self._momentum_vector, '平')
    
    @property
    def momentum_intensity(self) -> float:
        return self._momentum_intensity
    
    def set_temp_momentum(self, name: str, duration: int = 1):
        vec = {'散':(1,0),'升':(0,1),'聚':(-1,0),'降':(0,-1),'平':(0,0)}.get(name)
        if vec:
            self._momentum_vector = vec
            # 简化：不处理持续时间
    
    def set_amount_by_state(self, state: str):
        if state in QI_BASE:
            self.amount = QI_BASE[state]
    
    def set_state(self, s: str):
        if s in ['active','hidden','stored']:
            self.state = s
    
    def is_active(self) -> bool:
        return self.state == 'active' and self.amount > 10 and self.purity > 2
    
    def change(self, delta_amount: int, delta_purity: int = 0):
        self.amount = max(0, min(100, self.amount + delta_amount))
        self.purity = max(0, min(10, self.purity + delta_purity))

# ================== GanZhi 类 ==================
class GanZhi:
    GAN_WUXING = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
    ZHI_WUXING = {'寅':'木','卯':'木','巳':'火','午':'火','申':'金','酉':'金','亥':'水','子':'水','辰':'土','戌':'土','丑':'土','未':'土'}
    TOMB = {'木':'未','火':'戌','土':'辰','金':'丑','水':'辰'}   # 墓库
    
    def __init__(self, gan: str, zhi: str, qi: Optional[Qi] = None):
        self.gan = gan
        self.zhi = zhi
        self.gan_wuxing = self.GAN_WUXING[gan]
        self.zhi_wuxing = self.ZHI_WUXING[zhi]
        self.nayin_wuxing = NAYIN_MAP.get(gan+zhi, '土')
        self.qi = qi if qi else Qi(wuxing=self.nayin_wuxing, base_zhi=zhi)
    
    def update_qi_by_season(self, season: str):
        """根据季节设置旺衰、气量、动量"""
        state_map = {
            '春': {'木':'旺','火':'相','土':'死','金':'囚','水':'休'},
            '夏': {'木':'休','火':'旺','土':'相','金':'死','水':'囚'},
            '秋': {'木':'死','火':'囚','土':'休','金':'旺','水':'相'},
            '冬': {'木':'相','火':'死','土':'囚','金':'休','水':'旺'},
            '季夏': {'木':'囚','火':'休','土':'旺','金':'相','水':'死'}
        }
        prosperity = state_map.get(season, {}).get(self.nayin_wuxing, '休')
        self.qi.update_prosperity(prosperity)
        self.qi.apply_direction_modulation(self.zhi)
        self.qi.set_amount_by_state(prosperity)
    
    def update_state_by_kongwang(self, current_xun: str):
        """根据年柱旬设置空亡状态"""
        xun_kong = {
            '甲子': ['戌','亥'], '甲戌': ['申','酉'], '甲申': ['午','未'],
            '甲午': ['辰','巳'], '甲辰': ['寅','卯'], '甲寅': ['子','丑']
        }
        if current_xun in xun_kong and self.zhi in xun_kong[current_xun]:
            self.qi.set_state('hidden')
        elif self.qi.state == 'hidden':
            self.qi.set_state('active')
    
    def update_state_by_muku(self):
        """根据纳音五行和地支设置墓库状态"""
        tomb_zhi = self.TOMB.get(self.nayin_wuxing)
        if tomb_zhi and self.zhi == tomb_zhi:
            self.qi.set_state('stored')
        elif self.qi.state == 'stored':
            self.qi.set_state('active')
    
    def update_qi_state(self, current_xun: str):
        self.update_state_by_kongwang(current_xun)
        if self.qi.state != 'hidden':
            self.update_state_by_muku()
    
    def update_ganzhi(self, new_gan: str, new_zhi: str):
        """更新干支（用于流年、流月、流日）"""
        self.gan = new_gan
        self.zhi = new_zhi
        self.gan_wuxing = self.GAN_WUXING[new_gan]
        self.zhi_wuxing = self.ZHI_WUXING[new_zhi]
        self.nayin_wuxing = NAYIN_MAP.get(new_gan+new_zhi, '土')
        self.qi.wuxing = self.nayin_wuxing
        self.qi.base_zhi = new_zhi

# ================== TimeEngine 类 ==================
class TimeEngine:
    MONTHS = ['寅','卯','辰','巳','午','未','申','酉','戌','亥','子','丑']
    SEASON_MAP = {'寅':'春','卯':'春','辰':'春','巳':'夏','午':'夏','未':'夏',
                  '申':'秋','酉':'秋','戌':'秋','亥':'冬','子':'冬','丑':'冬'}
    # 节气近似日期（月,日）
    JIEQI_DATE = {
        '立春':(2,4),'惊蛰':(3,5),'清明':(4,4),'立夏':(5,5),
        '芒种':(6,5),'小暑':(7,7),'立秋':(8,7),'白露':(9,7),
        '寒露':(10,8),'立冬':(11,7),'大雪':(12,7),'小寒':(1,5)
    }
    MONTH_JIE = ['立春','惊蛰','清明','立夏','芒种','小暑','立秋','白露','寒露','立冬','大雪','小寒']
    
    def __init__(self, year_ganzhi: str, month_ganzhi: str, day_ganzhi: str, hour_ganzhi: str,
                 gender: str = 'male', birth_solar_date: tuple = None):
        # 四柱对象
        self.year_gz = GanZhi(year_ganzhi[0], year_ganzhi[1])
        self.month_gz = GanZhi(month_ganzhi[0], month_ganzhi[1])
        self.day_gz = GanZhi(day_ganzhi[0], day_ganzhi[1])
        self.hour_gz = GanZhi(hour_ganzhi[0], hour_ganzhi[1])
        self.all_ganzhi = [self.year_gz, self.month_gz, self.day_gz, self.hour_gz]
        
        self.gender = gender
        self.birth_solar_date = birth_solar_date
        
        self.current_year_ganzhi = year_ganzhi
        self.current_month_ganzhi = month_ganzhi
        self.current_day_ganzhi = day_ganzhi
        self.current_hour_ganzhi = hour_ganzhi
        self.current_month_zhi = month_ganzhi[1]
        self.current_season = self.SEASON_MAP.get(self.current_month_zhi, '春')
        self.current_xun = self._get_xun(year_ganzhi)
        self.age = 0
        
        self.major_luck_list = []      # [(start_age, ganzhi)]
        self.current_luck_index = -1
        
        self._update_all_qi()
    
    def _get_xun(self, ganzhi: str) -> str:
        stems = '甲乙丙丁戊己庚辛壬癸'
        branches = '子丑寅卯辰巳午未申酉戌亥'
        gan, zhi = ganzhi[0], ganzhi[1]
        gan_idx = stems.index(gan)
        zhi_idx = branches.index(zhi)
        start_zhi_idx = (zhi_idx - gan_idx) % 12
        start_zhi = branches[start_zhi_idx]
        xun_map = {'子':'甲子','戌':'甲戌','申':'甲申','午':'甲午','辰':'甲辰','寅':'甲寅'}
        return xun_map.get(start_zhi, '甲子')
    
    def _update_all_qi(self):
        for gz in self.all_ganzhi:
            gz.update_qi_by_season(self.current_season)
            gz.update_qi_state(self.current_xun)
    
    # 节气与月支修正
    def _is_jie_after(self, date: tuple, jie_name: str) -> bool:
        jm, jd = self.JIEQI_DATE[jie_name]
        y, m, d = date
        if m > jm:
            return True
        if m == jm and d >= jd:
            return True
        return False
    
    def _get_actual_month_zhi(self, date: tuple) -> str:
        for i, jie in enumerate(self.MONTH_JIE):
            if not self._is_jie_after(date, jie):
                return self.MONTHS[i-1] if i>0 else self.MONTHS[-1]
        return self.MONTHS[-1]
    
    def set_current_date(self, year: int, month: int, day: int):
        new_zhi = self._get_actual_month_zhi((year, month, day))
        if new_zhi != self.current_month_zhi:
            self.current_month_zhi = new_zhi
            new_gan = self._calc_month_gan(self.current_year_ganzhi[0], new_zhi)
            self.current_month_ganzhi = new_gan + new_zhi
            self.month_gz.update_ganzhi(new_gan, new_zhi)
            self.current_season = self.SEASON_MAP.get(new_zhi, '春')
            self._update_all_qi()
    
    # 大运起运计算
    def _days_to_next_jie(self, birth_date: tuple, target_jie: str) -> int:
        # 简化：返回固定天数（实际需精确计算）
        return 30
    
    def calculate_start_luck(self):
        if not self.birth_solar_date:
            raise ValueError("需要出生公历日期")
        year_gan = self.current_year_ganzhi[0]
        is_yang = year_gan in ['甲','丙','戊','庚','壬']
        if (is_yang and self.gender=='male') or (not is_yang and self.gender=='female'):
            direction = 'forward'
            idx = self.MONTHS.index(self.current_month_zhi)
            target_jie = self.MONTH_JIE[(idx+1)%12]
            days = self._days_to_next_jie(self.birth_solar_date, target_jie)
        else:
            direction = 'backward'
            idx = self.MONTHS.index(self.current_month_zhi)
            target_jie = self.MONTH_JIE[(idx-1)%12]
            days = self._days_to_next_jie(self.birth_solar_date, target_jie)
        start_age = days / 3.0
        self.major_luck_list = self._generate_luck_list(self.current_month_ganzhi, direction, start_age)
        self._update_current_luck()
    
    def _generate_luck_list(self, month_ganzhi: str, direction: str, start_age: float):
        gan_order = '甲乙丙丁戊己庚辛壬癸'
        zhi_order = '子丑寅卯辰巳午未申酉戌亥'
        mg, mz = month_ganzhi[0], month_ganzhi[1]
        luck = []
        for step in range(8):
            if direction == 'forward':
                ng = gan_order[(gan_order.index(mg) + step + 1) % 10]
                nz = zhi_order[(zhi_order.index(mz) + step + 1) % 12]
            else:
                ng = gan_order[(gan_order.index(mg) - step - 1) % 10]
                nz = zhi_order[(zhi_order.index(mz) - step - 1) % 12]
            luck.append((start_age + step*10, ng+nz))
        return luck
    
    def _update_current_luck(self):
        if not self.major_luck_list:
            self.current_luck_index = -1
            return
        for i, (sa, _) in enumerate(self.major_luck_list):
            if self.age >= sa:
                self.current_luck_index = i
            else:
                break
    
    def current_major_luck(self):
        if self.current_luck_index >= 0:
            return self.major_luck_list[self.current_luck_index][1]
        return None
    
    # 辅助函数
    @staticmethod
    def _next_gan(gan: str) -> str:
        order = '甲乙丙丁戊己庚辛壬癸'
        return order[(order.index(gan)+1)%10]
    
    @staticmethod
    def _next_zhi(zhi: str) -> str:
        order = '子丑寅卯辰巳午未申酉戌亥'
        return order[(order.index(zhi)+1)%12]
    
    @staticmethod
    def _calc_month_gan(year_gan: str, month_zhi: str) -> str:
        first = {'甲':'丙','己':'丙','乙':'戊','庚':'戊','丙':'庚','辛':'庚','丁':'壬','壬':'壬','戊':'甲','癸':'甲'}
        fg = first.get(year_gan, '丙')
        month_order = ['寅','卯','辰','巳','午','未','申','酉','戌','亥','子','丑']
        offset = (month_order.index(month_zhi) - month_order.index('寅')) % 12
        gan_order = '甲乙丙丁戊己庚辛壬癸'
        return gan_order[(gan_order.index(fg) + offset) % 10]
    
    # 时间推进
    def advance_year(self):
        ng = self._next_gan(self.current_year_ganzhi[0])
        nz = self._next_zhi(self.current_year_ganzhi[1])
        self.current_year_ganzhi = ng + nz
        self.year_gz.update_ganzhi(ng, nz)
        self.age += 1
        self.current_xun = self._get_xun(self.current_year_ganzhi)
        # 月干随年干变化
        new_mg = self._calc_month_gan(ng, self.current_month_zhi)
        self.current_month_ganzhi = new_mg + self.current_month_zhi
        self.month_gz.update_ganzhi(new_mg, self.current_month_zhi)
        self._update_all_qi()
        self._update_current_luck()
    
    def advance_month(self):
        idx = self.MONTHS.index(self.current_month_zhi)
        nxt = (idx + 1) % 12
        new_zhi = self.MONTHS[nxt]
        self.current_month_zhi = new_zhi
        new_gan = self._calc_month_gan(self.current_year_ganzhi[0], new_zhi)
        self.current_month_ganzhi = new_gan + new_zhi
        self.month_gz.update_ganzhi(new_gan, new_zhi)
        self.current_season = self.SEASON_MAP.get(new_zhi, '春')
        if new_zhi == '寅' and idx == 11:  # 跨年
            self.advance_year()
            return
        self._update_all_qi()
    
    def advance_day(self):
        ng = self._next_gan(self.current_day_ganzhi[0])
        nz = self._next_zhi(self.current_day_ganzhi[1])
        self.current_day_ganzhi = ng + nz
        self.day_gz.update_ganzhi(ng, nz)
        # 日柱变化一般不影响全局旺衰，但需更新空亡状态（若以日柱定空亡，可在此处理）
        self._update_all_qi()   # 可选，但为统一状态，保留

# ================== 示例用法 ==================
if __name__ == '__main__':
    # 创建时间引擎（年柱庚辰，月柱己卯，日柱甲子，时柱甲子，男，出生日期2000-03-05）
    engine = TimeEngine('庚辰', '己卯', '甲子', '甲子', gender='male', birth_solar_date=(2000,3,5))
    
    # 计算大运
    engine.calculate_start_luck()
    print(f"起运岁数: {engine.major_luck_list[0][0]:.1f}")
    print(f"第一步大运: {engine.major_luck_list[0][1]}")
    
    # 查看初始状态
    print(f"初始季节: {engine.current_season}")
    for gz in engine.all_ganzhi:
        print(f"{gz.gan}{gz.zhi} 气量:{gz.qi.amount} 动量:{gz.qi.momentum} 强度:{gz.qi.momentum_intensity:.2f} 状态:{gz.qi.state}")
    
    # 推进一年
    engine.advance_year()
    print(f"\n推进一年后，流年: {engine.current_year_ganzhi}, 季节: {engine.current_season}")
    
    # 推进一个月
    engine.advance_month()
    print(f"推进一个月后，流月: {engine.current_month_ganzhi}")
    
    # 模拟木生火（甲寅木 生 丙寅火）
    jia_yin = GanZhi('甲', '寅')
    bing_yin = GanZhi('丙', '寅')
    jia_yin.update_qi_by_season('春')
    bing_yin.update_qi_by_season('春')
    print(f"\n春季木火生克前: 木量={jia_yin.qi.amount}, 火量={bing_yin.qi.amount}")
    jia_yin.qi.interact_with_other(bing_yin.qi, 'generate')
    print(f"生后: 木量={jia_yin.qi.amount}, 火量={bing_yin.qi.amount}")