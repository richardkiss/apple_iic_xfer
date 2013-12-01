 ORG $8000
LOADAYRWTS = $3E3
CALLRWTS = $3D9

PRBYTE = $FDDA
COUT = $FDED

PTR = $4
ERROR = $6
RWPTR = $7
ADD = $2
EORSUM = $3
TRACK = $0
SECTOR = $1
BUFPAGE = $9
DEFBUFPG = $85

* MUST SET TRACK

RDTRK LDA #$F
 STA SECTOR
 CLC
 ADC #DEFBUFPG
 STA BUFPAGE
SLOOP JSR READSEC
 DEC BUFPAGE
 DEC SECTOR
 BPL SLOOP
* NOW PRINT IT
 LDA #"T"
 LDY TRACK
 JSR PRVAL
 LDA #DEFBUFPG
 STA BUFPAGE
 LDA #0
PLOOP PHA
 JSR PRSEC
 PLA
 TAY
 INC BUFPAGE
 INY
 TYA
 CPY #$10
 BLT PLOOP
 RTS

PRSEC LDY #0
 STY PTR
 STY ADD
 STY EORSUM
 LDA BUFPAGE
 STA PTR+1
PRLOOP LDA (PTR),Y
 PHA
 JSR PRBYTE
 PLA
 PHA
 CLC
 ADC ADD
 STA ADD
 PLA
 EOR EORSUM
 STA EORSUM
 INY
 TYA
 AND #$1F
 BNE NOCR
 JSR PRCR
NOCR TYA
 BNE PRLOOP
 LDA #"+"
 LDY ADD
 JSR PRVAL
 LDA #"E"
 LDY EORSUM
 JMP PRVAL

PRVAL JSR COUT
 LDA #"="
 JSR COUT
 TYA
 JSR PRBYTE
PRCR LDA #$8D
 JMP COUT

READSEC JSR LOADAYRWTS
 STY RWPTR
 STA RWPTR+1
 LDY #3
 LDA #0
 STA (RWPTR),Y ; SET VOLUME TO 0
 LDA TRACK
 INY
 STA (RWPTR),Y
 LDA SECTOR
 INY
 STA (RWPTR),Y
 LDA #0
 LDY #8
 STA (RWPTR),Y
 LDA BUFPAGE
 INY
 STA (RWPTR),Y
 LDA #1 ;COMMAND FOR READ
 LDY #$C
 STA (RWPTR),Y
 JSR LOADAYRWTS
 JSR CALLRWTS
 LDY #$D
 LDA (RWPTR),Y
 BCS ERR
 RTS
ERR JMP $FF59