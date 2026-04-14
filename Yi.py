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

    # ===== 气的本质扩展 =====
    # 气的品质分类
    QI_QUALITY = {
        '清气': {'purity_min': 8, 'effect': '升阳'},
        '浊气': {'purity_min': 0, 'purity_max': 3, 'effect': '降阴'},
        '正气': {'purity_min': 6, 'alignment': '阳', 'effect': '吉'},
        '邪气': {'purity_min': 0, 'purity_max': 4, 'alignment': '阴', 'effect': '凶'}
    }
    
    # 气与神煞关联
    QI_SHEN_SHA = {
        '天乙': {'wuxing': '土', 'quality': '清气', 'effect': '贵'},
        '太极': {'wuxing': '水', 'quality': '清气', 'effect': '智'},
        '文昌': {'wuxing': '木', 'quality': '正气', 'effect': '文'},
        '驿马': {'wuxing': '火', 'quality': '浊气', 'effect': '动'},
        '将星': {'wuxing': '金', 'quality': '正气', 'effect': '威'}
    }
    
    def get_quality(self) -> str:
        """获取气的品质分类"""
        if self.purity >= 8:
            return '清气'
        elif self.purity >= 6:
            return '正气'
        elif self.purity <= 3:
            return '浊气'
        else:
            return '普通'
    
    def get_alignment(self) -> str:
        """获取气的阴阳属性"""
        # 根据五行和纯度判断阴阳
        yang_wuxing = ['木', '火']
        yin_wuxing = ['金', '水']
        if self.wuxing in yang_wuxing:
            base = '阳'
        elif self.wuxing in yin_wuxing:
            base = '阴'
        else:
            base = '中'
        # 纯度影响阴阳偏向
        if self.purity >= 7:
            return base
        elif self.purity <= 3:
            return '阴' if base == '阳' else '阳'
        else:
            return base
    
    def get_shen_sha_affinity(self, shen_sha_name: str) -> float:
        """计算气与神煞的亲和度"""
        shen_info = self.QI_SHEN_SHA.get(shen_sha_name)
        if not shen_info:
            return 0.0
        # 五行匹配
        wuxing_match = 1.0 if self.wuxing == shen_info['wuxing'] else 0.3
        # 品质匹配
        quality = self.get_quality()
        quality_match = 1.0 if quality == shen_info['quality'] else 0.5
        # 纯度影响
        purity_factor = self.purity / 10.0
        return (wuxing_match * 0.4 + quality_match * 0.4 + purity_factor * 0.2)
    
    def transform_quality(self, target_quality: str, amount: int = 5):
        """转化气品质"""
        if target_quality == '清气':
            self.purity = min(10, self.purity + amount)
        elif target_quality == '浊气':
            self.purity = max(0, self.purity - amount)
        elif target_quality == '正气':
            self.purity = min(10, max(6, self.purity))
    
    def connect_to_dao(self, dao: Dao) -> dict:
        """连接道，获取气的道性"""
        balance = dao.check_balance(
            yin_force=10 - self.purity if self.get_alignment() == '阴' else 0,
            yang_force=self.purity if self.get_alignment() == '阳' else 0
        )
        return {
            'wuxing_phase': dao.get_wuxing_phase(self.wuxing),
            'yin_yang_balance': balance,
            'taiji_level': dao.taiji
        }
    
    def connect_to_de(self, de: De) -> dict:
        """连接德，获取气的德性"""
        virtue = de.get_virtue()
        return {
            'virtue': virtue,
            'integrity': de.integrity,
            'manifestation': de.manifestation * (self.purity / 10.0)
        }

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

    def get_shen_sha(self, ref_gan: str = None, ref_zhi: str = None) -> 'ShenSha':
        """获取神煞对象（默认以日柱为参考）"""
        # ShenSha类在文件后面定义，但运行时已加载
        return ShenSha(self.gan, self.zhi, ref_gan, ref_zhi)
    
    def calculate_shen_sha_list(self, ref_gan: str = None, ref_zhi: str = None) -> dict:
        """计算神煞列表"""
        shen_sha = self.get_shen_sha(ref_gan, ref_zhi)
        return shen_sha.shen_sha_list
    
    def apply_shen_sha_to_qi(self, ref_gan: str = None, ref_zhi: str = None):
        """应用神煞影响至气"""
        shen_sha = self.get_shen_sha(ref_gan, ref_zhi)
        shen_sha.affect_qi(self.qi)
    
    def get_de_object(self) -> De:
        """获取德对象（基于纳音五行）"""
        de = De(self.nayin_wuxing)
        # 根据气的纯度调整德性完整度
        de.integrity = max(1, min(10, self.qi.purity // 2))
        return de
    
    def get_dao_connection(self, dao: Dao) -> dict:
        """连接道，获取干支的道性"""
        # 五行相位
        wuxing_phase = dao.get_wuxing_phase(self.nayin_wuxing)
        # 阴阳平衡（基于天干地支阴阳）
        gan_yinyang = '阳' if self.gan in ['甲','丙','戊','庚','壬'] else '阴'
        zhi_yinyang = '阳' if self.zhi in ['子','寅','辰','午','申','戌'] else '阴'
        yin_force = 10 if gan_yinyang == '阴' or zhi_yinyang == '阴' else 0
        yang_force = 10 if gan_yinyang == '阳' or zhi_yinyang == '阳' else 0
        balance = dao.check_balance(yin_force, yang_force)
        return {
            'wuxing_phase': wuxing_phase,
            'yin_yang_balance': balance,
            'gan_yinyang': gan_yinyang,
            'zhi_yinyang': zhi_yinyang
        }
    
    def get_space_shen_sha(self, direction: str) -> dict:
        """获取空间神煞（基于方位）"""
        # 方位与地支对应
        direction_zhi = {
            '东': ['卯'], '南': ['午'], '西': ['酉'], '北': ['子'],
            '东南': ['辰','巳'], '西南': ['未','申'], '西北': ['戌','亥'], '东北': ['丑','寅']
        }
        affected = False
        for d, zhilist in direction_zhi.items():
            if direction == d and self.zhi in zhilist:
                affected = True
                break
        # 空间神煞影响
        space_effects = {
            '东': {'青龙': 0.8, '贵人': 0.6},
            '南': {'朱雀': 0.7, '文昌': 0.5},
            '西': {'白虎': -0.6, '杀': -0.8},
            '北': {'玄武': -0.5, '盗': -0.7}
        }
        effect = space_effects.get(direction, {})
        return {'affected': affected, 'effects': effect}

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

    def calculate_all_shen_sha(self) -> dict:
        """计算四柱神煞（以日柱为参考）"""
        day_gan = self.day_gz.gan
        day_zhi = self.day_gz.zhi
        year_zhi = self.year_gz.zhi
        
        shen_sha_results = {}
        for name, gz in zip(['年柱','月柱','日柱','时柱'], self.all_ganzhi):
            shen_sha = gz.get_shen_sha(ref_gan=day_gan, ref_zhi=year_zhi)
            shen_sha_results[name] = {
                '干支': f"{gz.gan}{gz.zhi}",
                '神煞': shen_sha.shen_sha_list,
                '吉神数': shen_sha.get_positive_count(),
                '凶煞数': shen_sha.get_negative_count()
            }
        return shen_sha_results
    
    def apply_shen_sha_to_all_qi(self):
        """应用神煞影响至所有气"""
        day_gan = self.day_gz.gan
        day_zhi = self.day_gz.zhi
        year_zhi = self.year_gz.zhi
        
        for gz in self.all_ganzhi:
            gz.apply_shen_sha_to_qi(ref_gan=day_gan, ref_zhi=year_zhi)
    
    def get_dao_for_system(self) -> Dao:
        """获取系统级的道对象"""
        dao = Dao()
        # 根据四柱阴阳平衡设置太极状态
        yin_count = 0
        yang_count = 0
        for gz in self.all_ganzhi:
            if gz.gan in ['甲','丙','戊','庚','壬']:
                yang_count += 1
            else:
                yin_count += 1
            if gz.zhi in ['子','寅','辰','午','申','戌']:
                yang_count += 1
            else:
                yin_count += 1
        dao.check_balance(yin_count, yang_count)
        dao.evolve_taiji(step=2)  # 假设已演化到阴阳阶段
        return dao
    
    def get_de_for_system(self) -> dict:
        """获取系统级的德性分析"""
        de_results = {}
        for name, gz in zip(['年柱','月柱','日柱','时柱'], self.all_ganzhi):
            de = gz.get_de_object()
            de_results[name] = {
                '干支': f"{gz.gan}{gz.zhi}",
                '五行': gz.nayin_wuxing,
                '德性': de.get_virtue(),
                '完整度': de.integrity,
                '显化度': de.manifestation
            }
        return de_results
    
    def get_space_shen_sha_for_directions(self) -> dict:
        """获取八个方位的空间神煞影响"""
        directions = ['东','南','西','北','东南','西南','西北','东北']
        results = {}
        for direction in directions:
            direction_effects = {}
            for gz in self.all_ganzhi:
                effect = gz.get_space_shen_sha(direction)
                if effect['affected']:
                    direction_effects[f"{gz.gan}{gz.zhi}"] = effect['effects']
            results[direction] = direction_effects
        return results
    
    def advance_with_shen_sha(self):
        """推进时间并更新神煞状态"""
        # 保存当前神煞状态
        old_shen_sha = self.calculate_all_shen_sha()
        # 推进时间（默认推进一天）
        self.advance_day()
        # 重新计算神煞
        new_shen_sha = self.calculate_all_shen_sha()
        # 应用神煞影响
        self.apply_shen_sha_to_all_qi()
        return {'old': old_shen_sha, 'new': new_shen_sha}

# ================== 道、德、神煞扩展 ==================
class Dao:
    """
    道：宇宙根本法则，阴阳五行生克制化之根本规律
    """
    # 阴阳属性
    YIN_YANG = {'阴': -1, '阳': 1}
    
    # 五行生克关系
    WUXING_GENERATE = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
    WUXING_RESTRICT = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}
    
    # 五行反生反克
    WUXING_REVERSE_GENERATE = {v: k for k, v in WUXING_GENERATE.items()}
    WUXING_REVERSE_RESTRICT = {v: k for k, v in WUXING_RESTRICT.items()}
    
    # 五行对应方位
    WUXING_DIRECTION = {'木': '东', '火': '南', '土': '中', '金': '西', '水': '北'}
    
    # 五行对应季节
    WUXING_SEASON = {'木': '春', '火': '夏', '土': '季夏', '金': '秋', '水': '冬'}
    
    def __init__(self):
        self.taiji = 0  # 太极状态，0为无极，1为太极，2为阴阳
        self.yin_yang_balance = 0.0  # 阴阳平衡度，-1为纯阴，1为纯阳
    
    def generate(self, wuxing: str) -> str:
        """五行相生"""
        return self.WUXING_GENERATE.get(wuxing, wuxing)
    
    def restrict(self, wuxing: str) -> str:
        """五行相克"""
        return self.WUXING_RESTRICT.get(wuxing, wuxing)
    
    def check_balance(self, yin_force: float, yang_force: float) -> float:
        """计算阴阳平衡度"""
        total = yin_force + yang_force
        if total == 0:
            return 0.0
        self.yin_yang_balance = (yang_force - yin_force) / total
        return self.yin_yang_balance
    
    def evolve_taiji(self, step: int = 1):
        """太极演化：无极→太极→阴阳→五行"""
        self.taiji = min(3, self.taiji + step)
    
    def get_wuxing_phase(self, wuxing: str, time_factor: float = 1.0) -> dict:
        """获取五行在当前时空下的相位状态"""
        # 相位包括：生、旺、墓、绝等
        phases = {
            '生': 0.2 * time_factor,
            '旺': 0.8 * time_factor,
            '墓': -0.3 * time_factor,
            '绝': -0.5 * time_factor
        }
        return phases


class De:
    """
    德：道的体现，五行之德，事物品质特性
    """
    # 五行之德
    WUXING_DE = {
        '木': {'德': '仁', '性': '曲直', '情': '仁慈', '色': '青', '味': '酸'},
        '火': {'德': '礼', '性': '炎上', '情': '恭敬', '色': '赤', '味': '苦'},
        '土': {'德': '信', '性': '稼穑', '情': '诚实', '色': '黄', '味': '甘'},
        '金': {'德': '义', '性': '从革', '情': '仗义', '色': '白', '味': '辛'},
        '水': {'德': '智', '性': '润下', '情': '智慧', '色': '黑', '味': '咸'}
    }
    
    # 五常之德
    WUCHANG = {'仁': '木', '义': '金', '礼': '火', '智': '水', '信': '土'}
    
    def __init__(self, wuxing: str = '土'):
        self.wuxing = wuxing
        self.virtue = self.WUXING_DE.get(wuxing, {})
        self.integrity = 5  # 德性完整度 1-10
        self.manifestation = 0.8  # 显化程度 0-1
    
    def get_virtue(self) -> dict:
        """获取五行对应的德性"""
        return self.virtue
    
    def get_wuxing_by_virtue(self, virtue: str) -> str:
        """根据德性获取五行"""
        return self.WUCHANG.get(virtue, '土')
    
    def cultivate(self, amount: int = 1):
        """修养德性"""
        self.integrity = min(10, self.integrity + amount)
    
    def degrade(self, amount: int = 1):
        """德性衰减"""
        self.integrity = max(1, self.integrity - amount)
    
    def manifest(self, factor: float = 0.1):
        """德性显化"""
        self.manifestation = min(1.0, self.manifestation + factor)
    
    def conceal(self, factor: float = 0.1):
        """德性隐藏"""
        self.manifestation = max(0.0, self.manifestation - factor)




# ================== 神煞类 ==================
class ShenSha:
    """
    神煞：吉神凶煞系统，基于干支、五行、节气计算
    """
    # 天乙贵人表（日干对应地支）
    TIANYI_GUI_REN = {
        '甲': ['丑','未'], '乙': ['子','申'], '丙': ['亥','酉'],
        '丁': ['亥','酉'], '戊': ['丑','未'], '己': ['子','申'],
        '庚': ['丑','未'], '辛': ['寅','午'], '壬': ['卯','巳'],
        '癸': ['卯','巳']
    }
    
    # 太极贵人表（日干对应地支）
    TAIJI_GUI_REN = {
        '甲': ['子','午'], '乙': ['子','午'], '丙': ['卯','酉'],
        '丁': ['卯','酉'], '戊': ['辰','戌','丑','未'], '己': ['辰','戌','丑','未'],
        '庚': ['寅','亥'], '辛': ['寅','亥'], '壬': ['申','巳'],
        '癸': ['申','巳']
    }
    
    # 文昌贵人表（日干对应地支）
    WENCHANG_GUI_REN = {
        '甲': ['巳'], '乙': ['午'], '丙': ['申'], '丁': ['酉'],
        '戊': ['申'], '己': ['酉'], '庚': ['亥'], '辛': ['子'],
        '壬': ['寅'], '癸': ['卯']
    }
    
    # 驿马表（年支对应地支）
    YI_MA = {
        '申': ['寅'], '子': ['寅'], '辰': ['寅'],
        '寅': ['申'], '午': ['申'], '戌': ['申'],
        '巳': ['亥'], '酉': ['亥'], '丑': ['亥'],
        '亥': ['巳'], '卯': ['巳'], '未': ['巳']
    }
    
    # 将星表（年支对应地支）
    JIANG_XING = {
        '寅': ['子'], '卯': ['卯'], '辰': ['辰'], '巳': ['巳'],
        '午': ['午'], '未': ['未'], '申': ['申'], '酉': ['酉'],
        '戌': ['戌'], '亥': ['亥'], '子': ['子'], '丑': ['丑']
    }
    
    # 华盖表（年支对应地支）
    HUA_GAI = {
        '寅': ['戌'], '卯': ['未'], '辰': ['辰'], '巳': ['丑'],
        '午': ['戌'], '未': ['未'], '申': ['辰'], '酉': ['丑'],
        '戌': ['戌'], '亥': ['未'], '子': ['辰'], '丑': ['丑']
    }
    
    # 劫煞表（年支对应地支）
    JIE_SHA = {
        '申': ['巳'], '子': ['巳'], '辰': ['巳'],
        '寅': ['亥'], '午': ['亥'], '戌': ['亥'],
        '巳': ['申'], '酉': ['申'], '丑': ['申'],
        '亥': ['寅'], '卯': ['寅'], '未': ['寅']
    }
    
    # 灾煞表（年支对应地支）
    ZAI_SHA = {
        '申': ['午'], '子': ['午'], '辰': ['午'],
        '寅': ['子'], '午': ['子'], '戌': ['子'],
        '巳': ['酉'], '酉': ['酉'], '丑': ['酉'],
        '亥': ['卯'], '卯': ['卯'], '未': ['卯']
    }
    
    # 岁煞表（年支对应地支）
    SUI_SHA = {
        '申': ['未'], '子': ['未'], '辰': ['未'],
        '寅': ['丑'], '午': ['丑'], '戌': ['丑'],
        '巳': ['辰'], '酉': ['辰'], '丑': ['辰'],
        '亥': ['戌'], '卯': ['戌'], '未': ['戌']
    }
    
    def __init__(self, gan: str, zhi: str, ref_gan: str = None, ref_zhi: str = None):
        """
        神煞计算基于目标干支（gan, zhi）和参考干支（通常为年柱或日柱）
        """
        self.gan = gan
        self.zhi = zhi
        self.ref_gan = ref_gan if ref_gan else gan
        self.ref_zhi = ref_zhi if ref_zhi else zhi
        self.shen_sha_list = self.calculate_all()
    
    def calculate_all(self) -> dict:
        """计算所有神煞"""
        return {
            '天乙贵人': self.is_tianyi_gui_ren(),
            '太极贵人': self.is_taiji_gui_ren(),
            '文昌贵人': self.is_wenchang_gui_ren(),
            '驿马': self.is_yi_ma(),
            '将星': self.is_jiang_xing(),
            '华盖': self.is_hua_gai(),
            '劫煞': self.is_jie_sha(),
            '灾煞': self.is_zai_sha(),
            '岁煞': self.is_sui_sha()
        }
    
    def is_tianyi_gui_ren(self) -> bool:
        """是否天乙贵人（以日干对地支）"""
        return self.zhi in self.TIANYI_GUI_REN.get(self.ref_gan, [])
    
    def is_taiji_gui_ren(self) -> bool:
        """是否太极贵人（以日干对地支）"""
        return self.zhi in self.TAIJI_GUI_REN.get(self.ref_gan, [])
    
    def is_wenchang_gui_ren(self) -> bool:
        """是否文昌贵人（以日干对地支）"""
        return self.zhi in self.WENCHANG_GUI_REN.get(self.ref_gan, [])
    
    def is_yi_ma(self) -> bool:
        """是否驿马（以年支对地支）"""
        return self.zhi in self.YI_MA.get(self.ref_zhi, [])
    
    def is_jiang_xing(self) -> bool:
        """是否将星（以年支对地支）"""
        return self.zhi in self.JIANG_XING.get(self.ref_zhi, [])
    
    def is_hua_gai(self) -> bool:
        """是否华盖（以年支对地支）"""
        return self.zhi in self.HUA_GAI.get(self.ref_zhi, [])
    
    def is_jie_sha(self) -> bool:
        """是否劫煞（以年支对地支）"""
        return self.zhi in self.JIE_SHA.get(self.ref_zhi, [])
    
    def is_zai_sha(self) -> bool:
        """是否灾煞（以年支对地支）"""
        return self.zhi in self.ZAI_SHA.get(self.ref_zhi, [])
    
    def is_sui_sha(self) -> bool:
        """是否岁煞（以年支对地支）"""
        return self.zhi in self.SUI_SHA.get(self.ref_zhi, [])
    
    def get_positive_count(self) -> int:
        """获取吉神数量"""
        positive = ['天乙贵人', '太极贵人', '文昌贵人', '将星']
        count = 0
        for name, exists in self.shen_sha_list.items():
            if name in positive and exists:
                count += 1
        return count
    
    def get_negative_count(self) -> int:
        """获取凶煞数量"""
        negative = ['劫煞', '灾煞', '岁煞']
        count = 0
        for name, exists in self.shen_sha_list.items():
            if name in negative and exists:
                count += 1
        return count
    
    def get_neutral_count(self) -> int:
        """获取中性神煞数量（驿马、华盖）"""
        neutral = ['驿马', '华盖']
        count = 0
        for name, exists in self.shen_sha_list.items():
            if name in neutral and exists:
                count += 1
        return count
    
    def get_shen_sha_strength(self, shen_sha_name: str) -> float:
        """获取神煞强度（0-1）"""
        if not self.shen_sha_list.get(shen_sha_name, False):
            return 0.0
        # 基础强度
        strength = 0.7
        # 干支生克影响
        # 简化：若神煞地支与目标干支五行相生则增强
        # 暂时返回固定值
        return strength
    
    def affect_qi(self, qi: Qi) -> Qi:
        """神煞对气的影响"""
        # 吉神增加气量纯度，凶煞减少
        positive_count = self.get_positive_count()
        negative_count = self.get_negative_count()
        delta_amount = positive_count * 3 - negative_count * 2
        delta_purity = positive_count * 1 - negative_count * 1
        qi.change(delta_amount, delta_purity)
        return qi

# ================== 空间神煞类 ==================
class SpaceShenSha:
    """
    空间神煞：方位相关的神煞系统，处理方位吉凶、风水神煞等
    """
    # 八方对应地支
    DIRECTION_ZHI = {
        '东': ['卯'],
        '东南': ['辰','巳'],
        '南': ['午'],
        '西南': ['未','申'],
        '西': ['酉'],
        '西北': ['戌','亥'],
        '北': ['子'],
        '东北': ['丑','寅']
    }
    
    # 八方神煞（吉凶）
    DIRECTION_SHEN_SHA = {
        '东': {'青龙': 0.8, '贵人': 0.6, '煞': -0.3},
        '东南': {'文昌': 0.7, '煞': -0.4},
        '南': {'朱雀': 0.6, '天喜': 0.5, '煞': -0.5},
        '西南': {'太岁': -0.7, '病符': -0.8},
        '西': {'白虎': -0.8, '杀': -0.9},
        '西北': {'天门': 0.4, '煞': -0.6},
        '北': {'玄武': -0.5, '盗': -0.7},
        '东北': {'鬼门': -0.8, '艮': 0.3}
    }
    
    # 二十四山方位（更精细）
    TWENTY_FOUR_MOUNTAINS = {
        '壬': ['子', 337.5, 352.5],
        '子': ['子', 352.5, 7.5],
        '癸': ['子', 7.5, 22.5],
        '丑': ['丑', 22.5, 37.5],
        '艮': ['丑', 37.5, 52.5],
        '寅': ['寅', 52.5, 67.5],
        '甲': ['寅', 67.5, 82.5],
        '卯': ['卯', 82.5, 97.5],
        '乙': ['卯', 97.5, 112.5],
        '辰': ['辰', 112.5, 127.5],
        '巽': ['辰', 127.5, 142.5],
        '巳': ['巳', 142.5, 157.5],
        '丙': ['巳', 157.5, 172.5],
        '午': ['午', 172.5, 187.5],
        '丁': ['午', 187.5, 202.5],
        '未': ['未', 202.5, 217.5],
        '坤': ['未', 217.5, 232.5],
        '申': ['申', 232.5, 247.5],
        '庚': ['申', 247.5, 262.5],
        '酉': ['酉', 262.5, 277.5],
        '辛': ['酉', 277.5, 292.5],
        '戌': ['戌', 292.5, 307.5],
        '乾': ['戌', 307.5, 322.5],
        '亥': ['亥', 322.5, 337.5]
    }
    
    def __init__(self, center_ganzhi: str = '甲子'):
        """
        center_ganzhi: 中心点干支（如房屋坐山、个人命宫等）
        """
        self.center_gan = center_ganzhi[0]
        self.center_zhi = center_ganzhi[1]
        self.center_wuxing = NAYIN_MAP.get(center_ganzhi, '土')
    
    def get_direction_effect(self, direction: str, target_ganzhi: str = None) -> dict:
        """获取方位对目标干支的影响"""
        target_gan = target_ganzhi[0] if target_ganzhi else self.center_gan
        target_zhi = target_ganzhi[1] if target_ganzhi else self.center_zhi
        
        # 方位地支
        direction_zhis = self.DIRECTION_ZHI.get(direction, [])
        affected = target_zhi in direction_zhis
        
        # 神煞影响
        shen_sha = self.DIRECTION_SHEN_SHA.get(direction, {})
        
        # 五行生克影响
        wuxing_effect = 0.0
        if direction_zhis:
            # 方位地支五行
            dir_wuxing = GanZhi.ZHI_WUXING.get(direction_zhis[0], '土')
            target_wuxing = NAYIN_MAP.get(target_gan+target_zhi, '土')
            # 生克关系
            if dir_wuxing == target_wuxing:
                wuxing_effect = 0.5
            elif self._is_generate(dir_wuxing, target_wuxing):
                wuxing_effect = 0.8
            elif self._is_restrict(dir_wuxing, target_wuxing):
                wuxing_effect = -0.6
        
        return {
            'affected': affected,
            'shen_sha': shen_sha,
            'wuxing_effect': wuxing_effect,
            'total_effect': sum(shen_sha.values()) + wuxing_effect
        }
    
    def get_twenty_four_mountain_effect(self, mountain: str, target_ganzhi: str) -> dict:
        """获取二十四山方位的影响"""
        if mountain not in self.TWENTY_FOUR_MOUNTAINS:
            return {}
        
        mountain_info = self.TWENTY_FOUR_MOUNTAINS[mountain]
        mountain_zhi = mountain_info[0]
        target_zhi = target_ganzhi[1]
        
        # 地支六合、六冲、三合等关系
        liuhe = {
            '子': '丑', '丑': '子',
            '寅': '亥', '亥': '寅',
            '卯': '戌', '戌': '卯',
            '辰': '酉', '酉': '辰',
            '巳': '申', '申': '巳',
            '午': '未', '未': '午'
        }
        liuchong = {
            '子': '午', '午': '子',
            '丑': '未', '未': '丑',
            '寅': '申', '申': '寅',
            '卯': '酉', '酉': '卯',
            '辰': '戌', '戌': '辰',
            '巳': '亥', '亥': '巳'
        }
        
        relationship = '普通'
        effect = 0.0
        if mountain_zhi == target_zhi:
            relationship = '同支'
            effect = 0.3
        elif liuhe.get(mountain_zhi) == target_zhi:
            relationship = '六合'
            effect = 0.8
        elif liuchong.get(mountain_zhi) == target_zhi:
            relationship = '六冲'
            effect = -0.7
        
        return {
            'mountain': mountain,
            'relationship': relationship,
            'effect': effect,
            'direction': self._get_direction_from_mountain(mountain)
        }
    
    def _get_direction_from_mountain(self, mountain: str) -> str:
        """从二十四山获取八方方位"""
        for dir_name, zhilist in self.DIRECTION_ZHI.items():
            for zhi in zhilist:
                if mountain in ['甲','乙','丙','丁','庚','辛','壬','癸']:
                    # 天干方位
                    if mountain in ['甲','乙'] and dir_name == '东':
                        return dir_name
                    elif mountain in ['丙','丁'] and dir_name == '南':
                        return dir_name
                    elif mountain in ['庚','辛'] and dir_name == '西':
                        return dir_name
                    elif mountain in ['壬','癸'] and dir_name == '北':
                        return dir_name
                else:
                    if mountain == zhi:
                        return dir_name
        return '中'
    
    @staticmethod
    def _is_generate(wuxing1: str, wuxing2: str) -> bool:
        """五行相生"""
        generate = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
        return generate.get(wuxing1) == wuxing2
    
    @staticmethod
    def _is_restrict(wuxing1: str, wuxing2: str) -> bool:
        """五行相克"""
        restrict = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}
        return restrict.get(wuxing1) == wuxing2
    
    def analyze_space_for_ganzhi(self, ganzhi: str, directions: list = None) -> dict:
        """分析干支在多个方位的空间神煞"""
        if directions is None:
            directions = list(self.DIRECTION_ZHI.keys())
        
        results = {}
        for direction in directions:
            effect = self.get_direction_effect(direction, ganzhi)
            results[direction] = effect
        
        # 找出最佳和最差方位
        best_dir = max(results.items(), key=lambda x: x[1]['total_effect'])
        worst_dir = min(results.items(), key=lambda x: x[1]['total_effect'])
        
        return {
            'ganzhi': ganzhi,
            'results': results,
            'best_direction': best_dir[0],
            'best_effect': best_dir[1]['total_effect'],
            'worst_direction': worst_dir[0],
            'worst_effect': worst_dir[1]['total_effect']
        }

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
    
    # ===== 道、德、神煞、空间神煞测试 =====
    print("\n" + "="*50)
    print("道、德、神煞、空间神煞测试")
    print("="*50)
    
    # 道测试
    dao = Dao()
    print(f"\n道 - 木生火: {dao.generate('木')}")
    print(f"道 - 木克土: {dao.restrict('木')}")
    print(f"道 - 阴阳平衡度: {dao.check_balance(3, 7):.2f}")
    
    # 德测试
    de = De('木')
    print(f"\n德 - 木之德: {de.get_virtue()}")
    de.cultivate(2)
    print(f"德 - 修养后完整度: {de.integrity}")
    
    # 神煞测试
    shen = ShenSha('甲', '子', ref_gan='甲', ref_zhi='寅')
    print(f"\n神煞 - 甲子 (参考甲寅): {shen.shen_sha_list}")
    print(f"吉神数量: {shen.get_positive_count()}")
    print(f"凶煞数量: {shen.get_negative_count()}")
    
    # 空间神煞测试
    space = SpaceShenSha('甲子')
    effect = space.get_direction_effect('东', '甲子')
    print(f"\n空间神煞 - 东方对甲子的影响: {effect}")
    
    # 时间引擎集成测试
    print("\n" + "="*50)
    print("时间引擎集成测试")
    print("="*50)
    shen_sha_results = engine.calculate_all_shen_sha()
    print(f"四柱神煞: {shen_sha_results}")
    de_results = engine.get_de_for_system()
    print(f"四柱德性: {de_results}")
    space_results = engine.get_space_shen_sha_for_directions()
    print(f"八方空间神煞: {space_results}")