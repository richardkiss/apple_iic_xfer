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
MAXBUF = $A
DEFBUFPG = $60
 
* MUST SET TRACK
 
RDTRK LDA #$F
 STA SECTOR
 LDA #$10
 STA MAXBUF
 CLC
 ADC #DEFBUFPG
 STA BUFPAGE
SLOOP JSR READSEC
 BCS ERR
 DEC BUFPAGE
 DEC SECTOR
 BPL SLOOP
 BMI PTRACK
 
* RWTS failed, so now read a raw track
ERR LDY #1
 LDA (RWPTR),Y
 TAX
 LDA $C089,X ; TURN ON DRIVE
* set up buffers
 DEY  ; Y = 0
 STY PTR
 LDA #DEFBUFPG
 STA PTR+1
 LDA #$1C
 STA BUFPAGE
 STA MAXBUF
SPINUP LDA $C08C,X
 CMP $C08C,X
 BEQ SPINUP
TRLOOP LDA $C08C,X
 BPL TRLOOP
 STA (PTR),Y
 INY
 BNE TRLOOP
 INC PTR+1
 DEC BUFPAGE
 BNE TRLOOP
* okay, we've read a track full of bytes
 
* NOW PRINT IT
PTRACK LDA #"T"
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
 CPY MAXBUF
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
 RTS
* it failed, so now let's use raw reads
