package com.zzh.oj.limit;

import com.zzh.oj.common.BusinessException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.stereotype.Component;

import java.util.Collections;

/**
 * 提交频率限制：同一用户每 N 秒最多提交 M 次
 *
 * 为什么要限流：判题要起子进程、编译、跑用例，是整套系统里最贵的操作。
 * 一个人疯狂点提交，就能把机器的 CPU 和进程数打满，所有人都用不了。
 */
@Slf4j
@Component
public class SubmitRateLimiter {

    private static final String KEY_PREFIX = "oj:submit:limit:";

    /**
     * INCR + 首次设置过期，放进一段 Lua 里执行。
     *
     * Redis 执行脚本是单线程的，中间不会插入别的命令，所以这两步是原子的。
     * 如果拆成两条命令发：INCR 完、EXPIRE 还没发，进程挂了 ——
     * 这个 key 就永远不会过期，这个用户被永久锁死。
     */
    private static final DefaultRedisScript<Long> SCRIPT = new DefaultRedisScript<>(
            "local c = redis.call('INCR', KEYS[1]) " +
                    "if c == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end " +
                    "return c",
            Long.class);

    private final StringRedisTemplate redis;
    private final int limit;
    private final int windowSeconds;

    public SubmitRateLimiter(StringRedisTemplate redis,
                             @Value("${oj.rate-limit.submit.limit:10}") int limit,
                             @Value("${oj.rate-limit.submit.window-seconds:60}") int windowSeconds) {
        this.redis = redis;
        this.limit = limit;
        this.windowSeconds = windowSeconds;
    }

    /**
     * 超限直接抛 429；Redis 不可用时放行（判题是核心功能，不能被限流组件拖死）
     */
    public void check(Long userId) {
        String key = KEY_PREFIX + userId;
        try {
            Long count = redis.execute(SCRIPT, Collections.singletonList(key),
                    String.valueOf(windowSeconds));

            if (count != null && count > limit) {
                throw new BusinessException(429,
                        "提交过于频繁，每 " + windowSeconds + " 秒最多 " + limit + " 次");
            }
        } catch (BusinessException e) {
            throw e;
        } catch (Exception e) {
            log.warn("Redis 不可用，本次跳过限流: {}", e.getMessage());
        }
    }
}
