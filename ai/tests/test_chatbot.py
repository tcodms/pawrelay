from ai.chatbot.engine import ChatbotEngine


def test_direct_entry():
    print("=== 직접 진입 테스트 ===")

    engine = ChatbotEngine()
    response = engine.get_current_response()
    print(f"1. 상태: {response['state']}, 질문: {response['message']}")
    assert response["state"] == "ASK_ORIGIN"

    response = engine.process_input("광주광역시")
    print(f"2. 상태: {response['state']}, 질문: {response['message']}")
    assert response["state"] == "ASK_DESTINATION"

    response = engine.process_input("서울특별시")
    print(f"3. 상태: {response['state']}, 질문: {response['message']}")
    assert response["state"] == "ASK_DATE"

    response = engine.process_input("2026-04-10")
    print(f"4. 상태: {response['state']}, 질문: {response['message']}")
    assert response["state"] == "ASK_VEHICLE"

    response = engine.process_input("있어요")
    print(f"5. 상태: {response['state']}, 질문: {response['message']}")
    assert response["state"] == "ASK_ANIMAL_SIZE"

    response = engine.process_input("중형 (5~15kg)")
    print(f"6. 상태: {response['state']}, 질문: {response['message']}")
    assert response["state"] == "CONFIRM"

    response = engine.process_input("등록하기")
    print(f"7. 상태: {response['state']}, 완료: {response['completed']}")
    assert response["completed"] is True
    print(f"   저장 데이터: {response['schedule_data']}")

    print("=== 직접 진입 테스트 성공 ===\n")


def test_post_entry():
    print("=== 게시판 진입 테스트 ===")

    auto_filled = {
        "available_date": "2026-04-10",
        "max_animal_size": "small",
    }
    engine = ChatbotEngine(post_id=5, auto_filled=auto_filled)

    response = engine.get_current_response()
    print(f"1. 상태: {response['state']}, 질문: {response['message']}")
    assert response["state"] == "ASK_ORIGIN"

    response = engine.process_input("광주광역시")
    print(f"2. 상태: {response['state']}, 질문: {response['message']}")
    assert response["state"] == "ASK_DESTINATION"

    response = engine.process_input("천안시")
    print(f"3. 상태: {response['state']}, 질문: {response['message']}")
    assert response["state"] == "ASK_VEHICLE"

    response = engine.process_input("없어요")
    print(f"4. 상태: {response['state']}, 질문: {response['message']}")
    assert response["state"] == "CONFIRM"

    response = engine.process_input("등록하기")
    print(f"5. 상태: {response['state']}, 완료: {response['completed']}")
    assert response["completed"] is True
    print(f"   저장 데이터: {response['schedule_data']}")

    print("=== 게시판 진입 테스트 성공 ===\n")


def test_invalid_input():
    print("=== 잘못된 입력 테스트 ===")

    engine = ChatbotEngine()

    response = engine.process_input("")
    print(f"빈 입력 → 에러: {response.get('error')}, 메시지: {response['message']}")
    assert response.get("error") == "INVALID_INPUT"

    print("=== 잘못된 입력 테스트 성공 ===\n")


def test_restart():
    print("=== 처음부터 다시 테스트 ===")

    engine = ChatbotEngine()
    engine.process_input("광주광역시")
    engine.process_input("서울특별시")
    engine.process_input("2026-04-10")
    engine.process_input("있어요")
    engine.process_input("중형 (5~15kg)")

    response = engine.process_input("처음부터 다시")
    print(f"리셋 후 상태: {response['state']}")
    assert response["state"] == "ASK_ORIGIN"

    print("=== 처음부터 다시 테스트 성공 ===\n")


if __name__ == "__main__":
    test_direct_entry()
    test_post_entry()
    test_invalid_input()
    test_restart()
    print("모든 테스트 통과!")