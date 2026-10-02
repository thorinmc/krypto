#include <windows.h>
#include <iostream>
#include <fstream>
#include <string>
#include <thread>
#include <chrono>

void ClickAt(int x, int y) {
    POINT p;
    GetCursorPos(&p);
    int oldX = p.x;
    int oldY = p.y;

    SetCursorPos(x, y);
    std::this_thread::sleep_for(std::chrono::milliseconds(200));

    INPUT inputs[2] = {};
    inputs[0].type = INPUT_MOUSE;
    inputs[0].mi.dwFlags = MOUSEEVENTF_LEFTDOWN;
    inputs[1].type = INPUT_MOUSE;
    inputs[1].mi.dwFlags = MOUSEEVENTF_LEFTUP;
    SendInput(2, inputs, sizeof(INPUT));

    SetCursorPos(oldX, oldY);
}

void PasteText(const std::string& text) {
    const size_t len = text.size() + 1;
    HGLOBAL hMem = GlobalAlloc(GMEM_MOVEABLE, len);
    memcpy(GlobalLock(hMem), text.c_str(), len);
    GlobalUnlock(hMem);
    OpenClipboard(0);
    EmptyClipboard();
    SetClipboardData(CF_TEXT, hMem);
    CloseClipboard();

    INPUT input[4] = {};
    input[0].type = INPUT_KEYBOARD;
    input[0].ki.wVk = VK_CONTROL;
    input[1].type = INPUT_KEYBOARD;
    input[1].ki.wVk = 'V';
    input[2].type = INPUT_KEYBOARD;
    input[2].ki.wVk = 'V';
    input[2].ki.dwFlags = KEYEVENTF_KEYUP;
    input[3].type = INPUT_KEYBOARD;
    input[3].ki.wVk = VK_CONTROL;
    input[3].ki.dwFlags = KEYEVENTF_KEYUP;

    SendInput(4, input, sizeof(INPUT));
}

int main() {
    std::ifstream file("message.txt");
    std::string message((std::istreambuf_iterator<char>(file)),
                        std::istreambuf_iterator<char>());
    file.close();

    int x = -1910; // Twoje X w ChatGPT
    int y = 460;   // Twoje Y w ChatGPT
    ClickAt(x, y);

    // Odczekaj 5 sekund przed wklejeniem wiadomości
    std::this_thread::sleep_for(std::chrono::seconds(5));

    PasteText(message);

    INPUT enter[2] = {};
    enter[0].type = INPUT_KEYBOARD;
    enter[0].ki.wVk = VK_RETURN;
    enter[1].type = INPUT_KEYBOARD;
    enter[1].ki.wVk = VK_RETURN;
    enter[1].ki.dwFlags = KEYEVENTF_KEYUP;
    SendInput(2, enter, sizeof(INPUT));

    return 0;
}