-- EVENT SCHEDULER
# 每月1号清空销售数据
CREATE EVENT clearMonthSold
  ON SCHEDULE
    EVERY 1 MONTH
    STARTS '2015-03-01 00:00:00'
DO
  UPDATE `shop__seller`
  SET `shop__seller`.`monthSold` = 0;

# 每分钟遍历商家start_time以自动营业
CREATE EVENT `start_seller`
  ON SCHEDULE
    EVERY 1 MINUTE
    STARTS '2015-03-01 00:00:00'
DO
  CALL `sellerStarter`();

# 每分钟遍历商家stop_time以自动歇业
CREATE EVENT `stop_seller`
  ON SCHEDULE
    EVERY 1 MINUTE
    STARTS '2015-03-01 00:00:00'
DO
  CALL `sellerStopper`();

# Stored procedure
# 遍历过程
CREATE PROCEDURE sellerStarter
  BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE sid, timeLength, i INT;
    DECLARE timeSeq TEXT;
    DECLARE curTime VARCHAR(9);
    DECLARE cur CURSOR FOR SELECT `id`,`start_time` FROM `shop__seller`;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN cur;

    read_loop: LOOP
      FETCH cur INTO sid, timeSeq;
      IF done THEN
        LEAVE read_loop;
      END IF;
      SELECT length(timeSeq) - length(replace(timeSeq, ',', '')) + 1 INTO timeLength;
      SET i = 1;
      WHILE i <= timeLength DO
        SET curTime = substring_index(substring_index(timeSeq, ',', i), ',', -1);
        IF substring_index(time(now()), ':', 2) = substring_index(time(curTime), ':', 2) THEN
          UPDATE `shop__seller` SET `shop__seller`.`status` = 1 WHERE `shop__seller`.`id` = sid;
        END IF;
        SET i = i + 1;
      END WHILE;
    END LOOP;

    CLOSE cur;
  END;

# 遍历过程
CREATE PROCEDURE sellerStopper
  BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE sid, timeLength, i INT;
    DECLARE timeSeq TEXT;
    DECLARE curTime VARCHAR(9);
    DECLARE cur CURSOR FOR SELECT `id`,`stop_time` FROM shop__seller`;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN cur;

    read_loop: LOOP
      FETCH cur INTO sid, timeSeq;
      IF done THEN
        LEAVE read_loop;
      END IF;
      SELECT length(timeSeq) - length(replace(timeSeq, ',', '')) + 1 INTO timeLength;
      SET i = 1;
      WHILE i <= timeLength DO
        SET curTime = substring_index(substring_index(timeSeq, ',', i), ',', -1);
        IF substring_index(time(now()), ':', 2) = substring_index(time(curTime), ':', 2) THEN
          UPDATE `shop__seller` SET `shop__seller`.`status` = 0 WHERE `shop__seller`.`id` = sid;
        END IF;
        SET i = i + 1;
      END WHILE;
    END LOOP;

    CLOSE cur;
  END;