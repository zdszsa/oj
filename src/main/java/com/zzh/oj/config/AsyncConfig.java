package com.zzh.oj.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import org.springframework.web.client.RestTemplate;

import java.util.concurrent.ThreadPoolExecutor;

/**
 * AI 评审专用线程池
 *
 * 为什么不直接用 @Async 默认的 SimpleAsyncTaskExecutor：
 * 它每次调用都新建一个线程，没有上限。大模型响应慢（几秒），
 * 请求一多线程数就爆了。这里固定 2 个线程 + 有界队列，
 * 队列满了直接拒绝（AI 是增强功能，丢了不影响判题）。
 */
@Configuration
@EnableAsync
public class AsyncConfig {

    @Bean("aiExecutor")
    public ThreadPoolTaskExecutor aiExecutor() {
        ThreadPoolTaskExecutor ex = new ThreadPoolTaskExecutor();
        ex.setCorePoolSize(2);
        ex.setMaxPoolSize(2);
        ex.setQueueCapacity(50);
        ex.setThreadNamePrefix("ai-review-");
        // 队列满了不阻塞调用方，直接拒绝 —— 判题不能被 AI 拖住
        ex.setRejectedExecutionHandler(new ThreadPoolExecutor.DiscardPolicy());
        ex.setWaitForTasksToCompleteOnShutdown(true);
        ex.setAwaitTerminationSeconds(5);
        ex.initialize();
        return ex;
    }

    /**
     * 调大模型用的 RestTemplate。
     * 必须显式设超时 —— 默认是无限等待，大模型卡住会把线程池占死。
     */
    @Bean
    public RestTemplate aiRestTemplate() {
        SimpleClientHttpRequestFactory f = new SimpleClientHttpRequestFactory();
        f.setConnectTimeout(5000);
        f.setReadTimeout(20000);
        return new RestTemplate(f);
    }
}
