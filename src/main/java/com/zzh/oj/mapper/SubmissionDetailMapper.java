package com.zzh.oj.mapper;

import com.zzh.oj.entity.SubmissionDetail;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface SubmissionDetailMapper {

    int insert(SubmissionDetail detail);

    SubmissionDetail selectBySubmissionId(Long submissionId);

    /** 判题后回填输出（编译错误 / 异常栈） */
    int updateOutput(@Param("submissionId") Long submissionId,
                     @Param("output") String output);

    /** AI 评审是异步的，单独回填 */
    int updateAiReview(@Param("submissionId") Long submissionId,
                       @Param("aiReview") String aiReview);
}
