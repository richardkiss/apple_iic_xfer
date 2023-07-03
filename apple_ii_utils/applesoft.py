import struct


APPLESOFT_TOKENS = (
    "END FOR NEXT DATA INPUT DEL DIM READ GR TEXT PR# IN# CALL "
    "PLOT HLIN VLIN HGR2 HGR HCOLOR= HPLOT DRAW XDRAW HTAB HOME "
    "ROT= SCALE= SHLOAD TRACE NOTRACE NORMAL INVERSE FLASH COLOR= "
    "POP VTAB HIMEM: LOMEM: ONERR RESUME RECALL STORE SPEED= LET "
    "GOTO RUN IF RESTORE & GOSUB RETURN REM STOP ON WAIT LOAD "
    "SAVE DEF POKE PRINT CONT LIST CLEAR GET NEW TAB( TO FN SPC( "
    "THEN AT NOT STEP + - * / ^ AND OR > = < SGN INT ABS USR FRE "
    "SCRN( PDL POS SQR RND LOG EXP COS SIN TAN ATN PEEK LEN STR$ "
    "VAL ASC CHR$ LEFT$ RIGHT$ MID$".split()
)


def list_applesoft(data):
    (length,) = struct.unpack("<H", data[:2])
    data = data[2 : 2 + length]
    lines = ["!A $%x" % length]
    ptr = 0
    while ptr < len(data) - 4:
        line_end, line_number = struct.unpack("<HH", data[ptr : ptr + 4])
        if line_end == 0:
            break
        ptr += 4
        current_line = ["%d " % line_number]
        while ptr < len(data):
            c = data[ptr]
            ptr += 1
            if c == 0:
                break
            if c >= 0x80:
                token_idx = c & 0x7F
                if token_idx < len(APPLESOFT_TOKENS):
                    c = " %s " % APPLESOFT_TOKENS[token_idx]
                else:
                    msg = f"unknown token: {c}"
                    raise ValueError(msg)
            else:
                c = chr(c)
            current_line.append(c)
        lines.append("".join(current_line))
    return "\n".join(lines)
