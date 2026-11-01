package com.zzh.oj.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
public class PingController {

    @GetMapping("/ping")
    public String ping() {
        return "pong";
    }


    @PostMapping("/echo")
    public String echo(@RequestBody Map<String,String> body){
        String x=body.get("text");
        if(x==null || x.isEmpty()){
            return "请求体缺少text字段";
        }
        return x;
    }
}
