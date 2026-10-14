"""
デフォルトSE生成スクリプト
耳に心地よく、ゲーム・配信を邪魔しないナチュラルな音色を生成します。
"""
import math
import wave
import struct
import os

SAMPLE_RATE = 44100

def create_tone(freqs, duration, attack=0.01, decay=0.1, sustain_level=0.5, release=0.1, wave_type="sine"):
    """
    指定された周波数の和音または単音からオーディオサンプルを生成する (ADSRエンベロープ付き)
    """
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    
    attack_samples = int(SAMPLE_RATE * attack)
    decay_samples = int(SAMPLE_RATE * decay)
    release_samples = int(SAMPLE_RATE * release)
    sustain_samples = max(0, total_samples - (attack_samples + decay_samples + release_samples))
    
    for i in range(total_samples):
        # ADSR エンベロープ計算
        if i < attack_samples:
            env = (i / attack_samples)
        elif i < attack_samples + decay_samples:
            d_progress = (i - attack_samples) / decay_samples
            env = 1.0 - (1.0 - sustain_level) * d_progress
        elif i < attack_samples + decay_samples + sustain_samples:
            env = sustain_level
        else:
            r_progress = (i - (attack_samples + decay_samples + sustain_samples)) / max(1, release_samples)
            env = max(0.0, sustain_level * (1.0 - r_progress))
            
        t = float(i) / SAMPLE_RATE
        val = 0.0
        for f in freqs:
            # 倍音を少し加えてリッチで温かみのあるベル/マリンバ風にする
            v1 = math.sin(2.0 * math.pi * f * t)
            v2 = 0.25 * math.sin(2.0 * math.pi * f * 2.0 * t)
            v3 = 0.08 * math.sin(2.0 * math.pi * f * 3.0 * t)
            val += (v1 + v2 + v3)
            
        val = (val / max(1, len(freqs))) * env
        samples.append(val)
        
    return samples

def write_wav(filename, samples):
    os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # モノラル
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(SAMPLE_RATE)
        
        # クリッピング防止 & ノーマライズ (最大振幅 0.85)
        max_val = max(abs(s) for s in samples) if samples else 1.0
        if max_val == 0:
            max_val = 1.0
        scale = 0.85 / max_val
        
        raw_data = bytearray()
        for s in samples:
            int_val = int(s * scale * 32767.0)
            int_val = max(-32768, min(32767, int_val))
            raw_data.extend(struct.pack('<h', int_val))
            
        wav_file.writeframes(raw_data)

def generate_default_sounds():
    out_dir = os.path.join(os.path.dirname(__file__), "sounds")
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. 勝利音 (victory.wav): ポロロンと駆け上がる明るいアルペジオ (C5 -> E5 -> G5 -> C6)
    c5, e5, g5, c6 = 523.25, 659.25, 783.99, 1046.50
    note_dur = 0.09
    tail_dur = 0.45
    
    # アルペジオを重ね合わせる
    total_len = int(SAMPLE_RATE * (note_dur * 3 + tail_dur))
    vic_samples = [0.0] * total_len
    
    notes = [c5, e5, g5, c6]
    for idx, freq in enumerate(notes):
        start_idx = int(SAMPLE_RATE * idx * note_dur)
        part = create_tone([freq], duration=tail_dur, attack=0.008, decay=0.12, sustain_level=0.3, release=0.25)
        for p_i, val in enumerate(part):
            if start_idx + p_i < total_len:
                vic_samples[start_idx + p_i] += val
                
    write_wav(os.path.join(out_dir, "victory.wav"), vic_samples)
    print("Generated victory.wav")
    
    # 2. 敗北音 (defeat.wav): 優しく落ち着いたトーン (柔らかいマイナーセブンスの余韻: A4 -> F4 -> D4)
    # 重すぎず、心地よく穏やかに反省・次へ切り替えられる丸い音
    def_total_len = int(SAMPLE_RATE * 0.9)
    def_samples = [0.0] * def_total_len
    def_notes = [587.33, 440.0, 349.23] # D5 -> A4 -> F4
    for idx, freq in enumerate(def_notes):
        start_idx = int(SAMPLE_RATE * idx * 0.12)
        part = create_tone([freq], duration=0.65, attack=0.02, decay=0.15, sustain_level=0.35, release=0.35)
        for p_i, val in enumerate(part):
            if start_idx + p_i < def_total_len:
                def_samples[start_idx + p_i] += val
    write_wav(os.path.join(out_dir, "defeat.wav"), def_samples)
    print("Generated defeat.wav")

    # 3. 共通通知音 (notify.wav): ピロッと軽快な2音チャイム (G5 -> C6)
    not_total_len = int(SAMPLE_RATE * 0.5)
    not_samples = [0.0] * not_total_len
    not_notes = [783.99, 1046.50]
    for idx, freq in enumerate(not_notes):
        start_idx = int(SAMPLE_RATE * idx * 0.08)
        part = create_tone([freq], duration=0.35, attack=0.008, decay=0.08, sustain_level=0.25, release=0.2)
        for p_i, val in enumerate(part):
            if start_idx + p_i < not_total_len:
                not_samples[start_idx + p_i] += val
    write_wav(os.path.join(out_dir, "notify.wav"), not_samples)
    print("Generated notify.wav")

if __name__ == "__main__":
    generate_default_sounds()
