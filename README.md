# timestamp

A simple timestamp tool.

## Requirements

The following packages are required by the main program.

```
pip3 install termcolor
```

## Example

```
$ timestamp 2020-08-27T06:18:34.942227194+07:00 1598458714.942227 1621593449863961 'Wed Aug 26 16:18:34 2020' 5daysago

------- (0) yyyymmdd_hhmmss_parser(2020-08-27T06:18:34.942227194+07:00) --------
            base(fmt):                               2020-08-27 06:18:34 +07:00
  Seconds since epoch:                                        1598458714.942227
 uSeconds since epoch:                                         1598458714942227
              rfc3339:                         2020-08-26T16:18:34.942227-07:00
              ctime():                                 Wed Aug 26 16:18:34 2020
        strftime(fmt):                                  2020-08-26 16:18:34 PDT
                Delta:                               -1233 days, 4:25:05.624493
   Day of Year (Week):                                                  239 (2)


---------------------- (1) time_parser(1598458714.942227) ----------------------
            base(fmt):                                  2020-08-26 09:18:34 PDT
  Seconds since epoch:                                        1598433514.942227
 uSeconds since epoch:                                         1598433514942227
              rfc3339:                         2020-08-26T09:18:34.942227-07:00
              ctime():                                 Wed Aug 26 09:18:34 2020
        strftime(fmt):                                  2020-08-26 09:18:34 PDT
                Delta:                              -1233 days, 11:25:05.624493
   Day of Year (Week):                                                  239 (2)


-------------------- (2) time_usec_parser(1621593449863961) --------------------
            base(fmt):                                  2021-05-21 03:37:29 PDT
  Seconds since epoch:                                        1621568249.863961
 uSeconds since epoch:                                         1621568249863961
              rfc3339:                         2021-05-21T03:37:29.863961-07:00
              ctime():                                 Fri May 21 03:37:29 2021
        strftime(fmt):                                  2021-05-21 03:37:29 PDT
                Delta:                               -965 days, 17:06:10.702759
   Day of Year (Week):                                                  141 (4)


------------------ (3) ctime_parser(Wed Aug 26 16:18:34 2020) ------------------
            base(fmt):                                  2020-08-26 16:18:34 PDT
  Seconds since epoch:                                        1598458714.000000
 uSeconds since epoch:                                         1598458714000000
              rfc3339:                                2020-08-26T16:18:34-07:00
              ctime():                                 Wed Aug 26 16:18:34 2020
        strftime(fmt):                                  2020-08-26 16:18:34 PDT
                Delta:                               -1233 days, 4:25:06.566720
   Day of Year (Week):                                                  239 (2)


-------------------------- (4) delta_parser(5daysago) --------------------------
            base(fmt):                                  2024-01-06 19:43:40 PST
  Seconds since epoch:                                        1704570220.566720
 uSeconds since epoch:                                         1704570220566720
              rfc3339:                         2024-01-06T19:43:40.566720-08:00
              ctime():                                 Sat Jan  6 19:43:40 2024
        strftime(fmt):                                  2024-01-06 19:43:40 PST
                Delta:                                         -5 days, 0:00:00
   Day of Year (Week):                                                    6 (5)


--------------------------- datetime.datetime.now() ----------------------------
            base(fmt):                                  2024-01-11 19:43:40 PST
  Seconds since epoch:                                        1705002220.566720
 uSeconds since epoch:                                         1705002220566720
              rfc3339:                         2024-01-11T19:43:40.566720-08:00
              ctime():                                 Thu Jan 11 19:43:40 2024
        strftime(fmt):                                  2024-01-11 19:43:40 PST
   Day of Year (Week):                                                   11 (3)
```
