'===============================
' CALL CENTER ANALYSIS MAKROSU - GÜNCELLENMİŞ
'===============================

Sub RunCallCenterAnalysis()

    Dim ws As Worksheet: Set ws = ThisWorkbook.Sheets("Data")
    Dim wb As Workbook: Set wb = ThisWorkbook

    Dim lastRow As Long: lastRow = ws.Cells(ws.Rows.Count, "A").End(xlUp).Row

    ' Sayfaları silip yeniden oluştur
    Dim sheetNames As Variant
    sheetNames = Array("Analysis", "Late Entry", "Early Break", "Early Logout", "Meeting Fail")
    
    Dim s As Variant
    For Each s In sheetNames
        On Error Resume Next
        Application.DisplayAlerts = False
        wb.Sheets(s).Delete
        Application.DisplayAlerts = True
        On Error GoTo 0
        wb.Sheets.Add(After:=wb.Sheets(wb.Sheets.Count)).Name = s
    Next s

    Dim shAN As Worksheet: Set shAN = wb.Sheets("Analysis")
    Dim shLE As Worksheet: Set shLE = wb.Sheets("Late Entry")
    Dim shEB As Worksheet: Set shEB = wb.Sheets("Early Break")
    Dim shEL As Worksheet: Set shEL = wb.Sheets("Early Logout")
    Dim shMF As Worksheet: Set shMF = wb.Sheets("Meeting Fail")

    ' Başlıklar
    shLE.Range("A1:B1") = Array("Date", "First Available")
    shEB.Range("A1:C1") = Array("Date", "Break Time", "Duration (s)")
    shEL.Range("A1:B1") = Array("Date", "Logout Time")
    shMF.Range("A1:C1") = Array("Date", "Time", "Duration (s)")

    ' Sayaçlar
    Dim countLE As Long, countEB As Long, countEL As Long, countMF As Long
    countLE = 0: countEB = 0: countEL = 0: countMF = 0

    Dim i As Long, rowStart As Long, rowEnd As Long
    rowStart = 2

    Do While rowStart <= lastRow

        Dim currentDate As String
        currentDate = ws.Cells(rowStart, "D").Text

        rowEnd = rowStart
        Do While rowEnd <= lastRow And ws.Cells(rowEnd, "D").Text = currentDate
            rowEnd = rowEnd + 1
        Loop

        Dim firstAvailableTime As Variant: firstAvailableTime = ""
        Dim earlyBreakLogged As Boolean: earlyBreakLogged = False
        Dim logoutTime As Variant: logoutTime = ""
        Dim hasLaterAvailable As Boolean: hasLaterAvailable = False

        ' Geç Giriş (ilk Available satırı aşağıdan yukarıya)
        For i = rowEnd - 1 To rowStart Step -1
            If ws.Cells(i, "A").Value = "Available" Then
                firstAvailableTime = ws.Cells(i, "E").Value
                If TimeValue(firstAvailableTime) > TimeValue("07:45:00") Then
                    countLE = countLE + 1
                    shLE.Cells(countLE + 1, 1).Value = currentDate
                    shLE.Cells(countLE + 1, 2).Value = firstAvailableTime
                End If
                Exit For
            End If
        Next i

        ' Erken Mola: Available sonrası 1 saat içinde Break
        If firstAvailableTime <> "" Then
            For i = rowEnd - 1 To rowStart Step -1
                If ws.Cells(i, "A").Value = "Break" Then
                    Dim breakTime As Variant: breakTime = ws.Cells(i, "E").Value
                    Dim durationText As String: durationText = Trim(ws.Cells(i, "F").Text)
                    Dim durSec As Long: durSec = DurationToSeconds(durationText)

                    If TimeValue(breakTime) <= TimeValue(firstAvailableTime) + TimeSerial(1, 0, 0) Then
                        countEB = countEB + 1
                        shEB.Cells(countEB + 1, 1).Value = currentDate
                        shEB.Cells(countEB + 1, 2).Value = breakTime
                        shEB.Cells(countEB + 1, 3).Value = durSec
                        Exit For
                    End If
                End If
            Next i
        End If

        ' Erken Çıkış (üstten aşağı): Eğer 16:25'ten önce logout varsa ve sonra tekrar login yoksa
        Dim lastLogoutRow As Long: lastLogoutRow = -1
        Dim hasAvailableAfterLogout As Boolean: hasAvailableAfterLogout = False

        For i = rowStart To rowEnd - 1
            If ws.Cells(i, "A").Value = "Logged Out" Then
                logoutTime = ws.Cells(i, "E").Value
                If TimeValue(logoutTime) < TimeValue("16:25:00") Then
                    lastLogoutRow = i
                End If
            End If
        Next i

        If lastLogoutRow <> -1 Then
            For i = lastLogoutRow + 1 To rowEnd - 1
                If ws.Cells(i, "A").Value = "Available" Then
                    hasAvailableAfterLogout = True
                    Exit For
                End If
            Next i
            If Not hasAvailableAfterLogout Then
                countEL = countEL + 1
                shEL.Cells(countEL + 1, 1).Value = currentDate
                shEL.Cells(countEL + 1, 2).Value = logoutTime
            End If
        End If

        ' Kısa Meeting/Training
        For i = rowStart To rowEnd - 1
            Dim st As String: st = ws.Cells(i, "A").Value
            If st = "Meeting" Or st = "Training" Then
                Dim dtext As String: dtext = Trim(ws.Cells(i, "F").Text)
                Dim s As Long: s = DurationToSeconds(dtext)
                If s > 0 And s < 900 Then
                    countMF = countMF + 1
                    shMF.Cells(countMF + 1, 1).Value = currentDate
                    shMF.Cells(countMF + 1, 2).Value = ws.Cells(i, "E").Value
                    shMF.Cells(countMF + 1, 3).Value = s
                End If
            End If
        Next i

        rowStart = rowEnd
    Loop

    ' ANALYSIS SHEET
    With shAN
        .Range("A1:B1").Value = Array("Kategori", "Sayi")
        .Cells(2, 1).Value = "Geç Giris": .Cells(2, 2).Value = countLE
        .Cells(3, 1).Value = "Erken Mola (Ilk 1 saat içinde Break)": .Cells(3, 2).Value = countEB
        .Cells(4, 1).Value = "Erken Çikis (16:25'ten önce)": .Cells(4, 2).Value = countEL
        .Cells(5, 1).Value = "Kısa Meeting/Training (<15dk)": .Cells(5, 2).Value = countMF
    End With

    MsgBox "✅ Günlük bazlı analiz tamamlandi!", vbInformation

End Sub

Function DurationToSeconds(ByVal t As String) As Long
    On Error GoTo errhandler
    Dim parts() As String
    t = Trim(t)
    If InStr(1, t, ":") = 0 Then DurationToSeconds = 0: Exit Function
    parts = Split(t, ":")
    If UBound(parts) = 2 Then
        DurationToSeconds = CLng(parts(0)) * 3600 + CLng(parts(1)) * 60 + CLng(parts(2))
    ElseIf UBound(parts) = 1 Then
        DurationToSeconds = CLng(parts(0)) * 60 + CLng(parts(1))
    Else
        DurationToSeconds = 0
    End If
    Exit Function
errhandler:
    DurationToSeconds = 0
End Function
