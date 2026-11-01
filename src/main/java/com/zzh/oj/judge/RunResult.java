package com.zzh.oj.judge;

public class RunResult {

    private final JudgeStatus status;
    private final String output;
    private final long timeMs;

    public RunResult(JudgeStatus status, String output, long timeMs) {
        this.status = status;
        this.output = output;
        this.timeMs = timeMs;
    }

    public JudgeStatus getStatus() { return status; }
    public String getOutput()    { return output; }
    public long getTimeMs()      { return timeMs; }

    @Override
    public String toString() {
        return status + " | " + timeMs + "ms | " + output.trim();
    }
}
