# timestamp

A simple timestamp tool.

## Requirements

The following packages are required by the main program.

```
pip install termcolor
pip install pytz
```

## Example

```
$ timestamp 2020-08-27T06:18:34.942227194+07:00 1598458714.942227 1621593449863961 'Wed Aug 26 16:18:34 2020' 5daysago

---------------------- (1) timeParser(1598458714.942227) -----------------------
            base(fmt):                                  2020-08-26 09:18:34 PDT
  Seconds since epoch:                                        1598433514.942227
 uSeconds since epoch:                                         1598433514942227
              rfc3339:                         2020-08-26T09:18:34.942227-07:00
              ctime():                                 Wed Aug 26 09:18:34 2020
        strftime(fmt):                                  2020-08-26 09:18:34 PDT
                Delta:                                -268 days, 1:19:33.282303
   Day of Year (Week):                                                  239 (2)

-------- (0) yyyyMmDdHhMmSsParser(2020-08-27T06:18:34.942227194+07:00) ---------
            base(fmt):                               2020-08-27 06:18:34 +07:00
  Seconds since epoch:                                        1598458714.942227
 uSeconds since epoch:                                         1598458714942227
              rfc3339:                         2020-08-26T16:18:34.942227-07:00
              ctime():                                 Wed Aug 26 16:18:34 2020
        strftime(fmt):                                  2020-08-26 16:18:34 PDT
                Delta:                               -267 days, 18:19:33.282303
   Day of Year (Week):                                                  239 (2)

------------------ (3) ctimeParser(Wed Aug 26 16:18:34 2020) -------------------
            base(fmt):                                  2020-08-26 16:18:34 LMT
  Seconds since epoch:                                        1598461894.000000
 uSeconds since epoch:                                         1598461894000000
              rfc3339:                                2020-08-26T17:11:34-07:00
              ctime():                                 Wed Aug 26 17:11:34 2020
        strftime(fmt):                                  2020-08-26 17:11:34 PDT
                Delta:                               -267 days, 17:26:34.224530
   Day of Year (Week):                                                  239 (2)

-------------------------- (4) deltaParser(5daysago) ---------------------------
            base(fmt):                                  2021-05-16 10:38:08 PDT
  Seconds since epoch:                                        1621161488.224530
 uSeconds since epoch:                                         1621161488224530
              rfc3339:                         2021-05-16T10:38:08.224530-07:00
              ctime():                                 Sun May 16 10:38:08 2021
        strftime(fmt):                                  2021-05-16 10:38:08 PDT
                Delta:                                         -5 days, 0:00:00
   Day of Year (Week):                                                  136 (6)

--------------------- (2) timeUsecParser(1621593449863961) ---------------------
            base(fmt):                                  2021-05-21 03:37:29 PDT
  Seconds since epoch:                                        1621568249.863961
 uSeconds since epoch:                                         1621568249863961
              rfc3339:                         2021-05-21T03:37:29.863961-07:00
              ctime():                                 Fri May 21 03:37:29 2021
        strftime(fmt):                                  2021-05-21 03:37:29 PDT
                Delta:                                          -7:00:38.360569
   Day of Year (Week):                                                  141 (4)

--------------------------- datetime.datetime.now() ----------------------------
            base(fmt):                                  2021-05-21 10:38:08 PDT
  Seconds since epoch:                                        1621593488.224530
 uSeconds since epoch:                                         1621593488224530
              rfc3339:                         2021-05-21T10:38:08.224530-07:00
              ctime():                                 Fri May 21 10:38:08 2021
        strftime(fmt):                                  2021-05-21 10:38:08 PDT
   Day of Year (Week):                                                  141 (4)
```
