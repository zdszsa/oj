package com.zzh.oj.ai;

import com.zzh.oj.mapper.SubmissionDetailMapper;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.List;
import java.util.Map;

/**
 * AI 代码评审
 *
 * 设计要点（面试会问）：
 * 1. 异步：大模型要几秒，同步会占住 Tomcat 线程、把判题结果也拖慢
 * 2. 降级：没配 Key / 调用失败，都只是没有点评，判题结果照常返回
 * 3. 有界线程池：AI 慢，线程数必须固定，不然并发一高线程爆炸
 */
@Slf4j
@Service
public class AiReviewService {

    @Value("${oj.ai.enabled:false}")
    private boolean enabled;

    /** 本地没 Key 时打开，用固定文案跑通链路 */
    @Value("${oj.ai.mock:false}")
    private boolean mock;

    @Value("${oj.ai.api-key:}")
    private String apiKey;

    @Value("${oj.ai.base-url:https://dashscope.aliyuncs.com/compatible-mode/v1}")
    private String baseUrl;

    @Value("${oj.ai.model:qwen-plus}")
    private String model;

    private final RestTemplate restTemplate;
    private final SubmissionDetailMapper detailMapper;

    @Resource(name = "aiExecutor")
    private ThreadPoolTaskExecutor aiExecutor;

    public AiReviewService(RestTemplate aiRestTemplate, SubmissionDetailMapper detailMapper) {
        this.restTemplate = aiRestTemplate;
        this.detailMapper = detailMapper;
    }

    /**
     * 提交评审任务，立刻返回。真正的调用在线程池里跑。
     */
    public void reviewAsync(Long submissionId, String problemTitle, String code) {
        if (!enabled) {
            return;
        }
        if (!mock && (apiKey == null || apiKey.isBlank())) {
            log.debug("AI 评审已开启但没有配置 api-key，跳过");
            return;
        }

        aiExecutor.execute(() -> {
            try {
                String review = mock ? mockReview() : callModel(problemTitle, code);
                detailMapper.updateAiReview(submissionId, review);
                log.info("AI 评审完成 submissionId={}", submissionId);
            } catch (Exception e) {
                // AI 失败不能影响任何东西，只记日志
                log.warn("AI 评审失败 submissionId={}: {}", submissionId, e.getMessage());
            }
        });
    }

    private String callModel(String problemTitle, String code) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.setBearerAuth(apiKey);

        Map<String, Object> body = Map.of(
                "model", model,
                "temperature", 0.3,
                "max_tokens", 400,
                "messages", List.of(
                        Map.of("role", "system", "content",
                                "你是一个 Java 代码评审助手。点评要简洁、具体、对事不对人，"
                                        + "不要给出完整答案，也不要重写整段代码。"),
                        Map.of("role", "user", "content", buildPrompt(problemTitle, code))
                )
        );

        ResponseEntity<Map> resp = restTemplate.postForEntity(
                baseUrl + "/chat/completions", new HttpEntity<>(body, headers), Map.class);

        Map data = resp.getBody();
        if (data == null) {
            throw new IllegalStateException("大模型返回为空");
        }
        List choices = (List) data.get("choices");
        if (choices == null || choices.isEmpty()) {
            throw new IllegalStateException("大模型返回没有 choices");
        }
        Map first = (Map) choices.get(0);
        Map message = (Map) first.get("message");
        Object content = message == null ? null : message.get("content");
        if (content == null) {
            throw new IllegalStateException("大模型返回没有 content");
        }
        return content.toString().trim();
    }

    private String buildPrompt(String problemTitle, String code) {
        return """
                题目：%s

                用户提交的 Java 代码：
                ```java
                %s
                ```

                请从三个方面点评，总共不超过 150 字：
                1. 时间复杂度，以及是否有更优解法
                2. 潜在的 bug 或边界问题
                3. 一点代码风格建议

                不要给出完整答案，不要重写代码。
                """.formatted(problemTitle, code);
    }

    private String mockReview() {
        return "【模拟点评】时间复杂度 O(n log n)，可以考虑用哈希表优化到 O(n)。"
                + "边界情况建议处理空输入。变量命名可以更语义化一些。";
    }
}
