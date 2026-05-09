Speech to text

const fs = require('fs-extra');
const path = require('path');
const memoryEngine = require('../memory_engine/memoryEngine');

const longTermPath = path.join(__dirname, '../memory_engine/long_term_memory.json');

exports.getLongTermMemory = (req, res) => {
    if (!fs.existsSync(longTermPath)) {
        return res.json([]);
    }
    const data = JSON.parse(fs.readFileSync(longTermPath));
    res.json(data);
};

exports.addMemory = (req, res) => {
    const { key, value, relation, nodeA, nodeB } = req.body;

    const entry = {
        key,
        value,
        created: new Date().toISOString()
    };

    memoryEngine.addLongTermMemory(entry);

    if (relation && nodeA && nodeB) {
        memoryEngine.addGraphRelation(nodeA, relation, nodeB);
    }

    res.json({ success: true });
};

exports.getConversationHistory = (req, res) => {
    const { userId } = req.params;

    const conversationPath = path.join(__dirname, '../memory_engine/conversations.json');

    if (!fs.existsSync(conversationPath)) {
        fs.writeJsonSync(conversationPath, {});
        return res.json({ success: true, messages: [] });
    }

    const allConversations = fs.readJsonSync(conversationPath);
    const userMessages = allConversations[userId] || [];

    res.json({
        success: true,
        messages: userMessages
    });
};

exports.saveMessage = (req, res) => {
    const { userId, sender, message } = req.body;

    const conversationPath = path.join(__dirname, '../memory_engine/conversations.json');

    let allConversations = {};
    if (fs.existsSync(conversationPath)) {
        allConversations = fs.readJsonSync(conversationPath);
    }

    if (!allConversations[userId]) {
        allConversations[userId] = [];
    }

    allConversations[userId].push({
        sender: sender,
        message: message,
        timestamp: new Date().toISOString()
    });

    fs.writeJsonSync(conversationPath, allConversations, { spaces: 2 });

    res.json({ success: true });
};